import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "local.free-hands"
  implicitWidth: icon.implicitWidth
  implicitHeight: icon.implicitHeight

  property var task: ({})
  property string dismissedTaskId: ""
  property bool pinned: false
  property bool expired: false
  readonly property string taskId: typeof task.id === "string" ? task.id : ""
  readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/free-hands"
  readonly property bool working: task.state === "working" || task.state === "cancelling"
  readonly property bool dockToLeft: task.corner === "top-left"
  readonly property bool canFollow: /^[0-9a-fA-F-]{36}$/.test(task.thread_id || "")
  readonly property bool hasChart: task.state === "done" && task.chart === true && /^[a-f0-9]{32}$/.test(task.id || "")
  readonly property string chartPath: runtimeDir + "/chart.svg"
  readonly property string executable: Quickshell.env("HOME") + "/.local/bin/free-hands"
  // Keep the target monitor independent from PanelWindow.screen to avoid a
  // visible/screen binding loop while Quickshell reloads local plugins.
  readonly property var monitor: Quickshell.screens[0]

  Translations { id: strings; directory: Qt.resolvedUrl("i18n") }

  function dismissCard() {
    dismissedTaskId = taskId;
    pinned = false;
  }

  function toggleCard() {
    if (card.visible)
      dismissCard();
    else
      pinned = true;
  }

  function runAction(action) {
    if (actionProc.running || !/^[a-f0-9]{32}$/.test(task.id || ""))
      return;
    actionProc.command = action === "follow" ? [executable, "follow", task.id] : [executable, action, "--task-id", task.id];
    actionProc.running = true;
  }

  Process {
    id: actionProc
  }
  Process {
    id: chartViewer
    command: ["xdg-open", root.chartPath]
  }
  ShellIpc {
    target: "local.free-hands"
    function toggle(): void {
      root.toggleCard();
    }
  }

  FileView {
    path: root.runtimeDir + "/task.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        const content = text();
        if (content.length > 4096)
          return;
        const next = JSON.parse(content);
        const changed = next.state !== root.task.state || next.id !== root.task.id;
        root.task = next;
        if (changed) {
          root.expired = false;
          expiry.stop();
          if (next.state === "done" || next.state === "error" || next.state === "cancelled")
            expiry.start();
        }
      } catch (error) {
        root.task = ({});
      }
    }
    onLoadFailed: root.task = ({})
  }

  Timer {
    id: expiry
    interval: root.hasChart || root.task.camera_session || root.task.screen_session ? 20000 : 8500
    onTriggered: root.expired = true
  }

  BarIconButton {
    id: icon
    anchors.fill: parent
    bar: root.bar
    text: root.working ? "\uf110" : "\uf120"
    slotSize: Style.bar.statusSlot
    tooltipText: "Seguimiento de DOOM"
    onPressed: root.toggleCard()
  }

  PanelWindow {
    id: card
    screen: root.monitor
    visible: root.pinned || (root.taskId !== "" && root.dismissedTaskId !== root.taskId
      && (root.working || (!root.expired && ["done", "cancelled", "error"].includes(root.task.state))))
    anchors.top: true
    anchors.left: root.dockToLeft
    anchors.right: !root.dockToLeft
    margins.top: 8
    margins.left: root.dockToLeft ? 10 : 0
    margins.right: root.dockToLeft ? 0 : 10
    implicitWidth: 310
    implicitHeight: layout.implicitHeight + 26
    exclusionMode: ExclusionMode.Normal
    exclusiveZone: 0
    WlrLayershell.namespace: "free-hands-tracker"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: grab.containsMouse ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    color: "transparent"

    Rectangle {
      anchors.fill: parent
      radius: 10
      border.color: root.working ? Color.accent : Color.muted
      gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.tint(Color.background, Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.08)) }
        GradientStop { position: 1.0; color: Color.background }
      }
    }

    Rectangle {
      id: closeButton
      z: 3
      visible: card.visible
      anchors.top: parent.top
      anchors.right: parent.right
      anchors.topMargin: 6
      anchors.rightMargin: 6
      width: 24
      height: 24
      radius: 12
      color: closeArea.containsMouse ? Color.urgent : "transparent"

      Text {
        anchors.centerIn: parent
        textFormat: Text.PlainText
        text: "×"
        color: closeArea.containsMouse ? Color.background : Color.foreground
        font.pixelSize: 18
        font.bold: true
      }

      MouseArea {
        id: closeArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.dismissCard()
      }
    }

    Rectangle {
      z: 3
      visible: (root.working || root.task.state === "done") && !root.hasChart
        && !root.task.camera_session && !root.task.screen_session
        && /^[a-f0-9]{32}$/.test(root.task.id || "")
      anchors.right: closeButton.left
      anchors.top: closeButton.top
      anchors.rightMargin: 4
      width: muteLabel.implicitWidth + 12
      height: closeButton.height
      radius: 6
      color: muteArea.containsMouse ? Color.muted : Color.background

      Text {
        id: muteLabel
        anchors.centerIn: parent
        textFormat: Text.PlainText
        text: strings.t(root.task.muted === true ? "muted" : "mute")
        color: Color.foreground
      }
      MouseArea {
        id: muteArea
        anchors.fill: parent
        enabled: root.task.muted !== true
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        onClicked: root.runAction("mute")
      }
    }

    Column {
      id: layout
      x: 13
      y: 13
      width: card.width - 26
      spacing: 8
      Text {
        textFormat: Text.PlainText
        text: root.working ? "DOOM · Trabajando" : "DOOM"
        color: Color.accent
        font.bold: true
      }
      Repeater {
        model: ["camera", "screen"]
        Column {
          id: captureView
          required property string modelData
          readonly property bool webcam: modelData === "camera"
          readonly property string info: root.task[modelData + "_session"] || ""
          readonly property string session: /^(camera|screen)-[a-z0-9_]{8}$/.test(info) ? info : ""
          readonly property bool active: root.task[modelData + "_active"] === true
          readonly property int frame: bounded("frame", 100)
          readonly property int count: bounded("shots", 4)
          width: layout.width
          spacing: 5
          visible: session !== ""

          function bounded(field, max) {
            const value = root.task[modelData + "_" + field];
            return Number.isInteger(value) && value > 0 && value <= max ? value : 0;
          }
          function frameUrl(name) {
            return card.visible && session ? "file://" + root.runtimeDir + "/" + session + "/" + name : "";
          }
          onCountChanged: if (count > 0 && visible) flash.restart()

          Rectangle {
            width: parent.width
            height: root.task.camera_session && root.task.screen_session ? 105 : 155
            radius: 6
            clip: true
            color: Color.background
            Image {
              anchors.fill: parent
              asynchronous: true
              retainWhileLoading: true
              fillMode: Image.PreserveAspectFit
              cache: false
              sourceSize.width: 448
              source: !captureView.frame ? "" : captureView.frameUrl(captureView.webcam
                ? "preview-" + (captureView.frame % 3) + ".jpg?v=" + captureView.frame
                : "shot-" + captureView.count + ".jpg")
            }
            Text {
              x: 8
              y: 5
              padding: 4
              textFormat: Text.PlainText
              text: strings.t(captureView.webcam
                ? (captureView.active ? "cameraLive" : "cameraDone")
                : (captureView.active ? "screenLive" : "screenDone"))
              color: Color.foreground
              Rectangle {
                anchors.fill: parent
                z: -1
                radius: 4
                color: Color.background
              }
            }
            Rectangle {
              id: exposure
              anchors.fill: parent
              color: "white"
              opacity: 0
              NumberAnimation {
                id: flash
                target: exposure
                property: "opacity"
                from: 0.48
                to: 0
                duration: Style.duration(150)
                easing.type: Easing.OutCubic
              }
            }
          }
          Row {
            id: shots
            width: parent.width
            spacing: 4
            Repeater {
              model: 4
              Rectangle {
                id: shotTile
                required property int index
                readonly property int number: index + 1
                readonly property bool captured: captureView.count >= number
                width: (shots.width - 3 * shots.spacing) / 4
                height: 52
                radius: 5
                color: Color.background
                border.color: still.status === Image.Ready ? Color.accent : Color.muted
                Image {
                  id: still
                  anchors.fill: parent
                  anchors.margins: 2
                  asynchronous: true
                  fillMode: Image.PreserveAspectFit
                  sourceSize.width: 144
                  opacity: status === Image.Ready ? 1 : 0
                  Behavior on opacity {
                    NumberAnimation { duration: Style.duration(130); easing.type: Easing.OutCubic }
                  }
                  cache: false
                  source: shotTile.captured ? captureView.frameUrl("shot-" + shotTile.number + ".jpg") : ""
                }
                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  anchors.bottom: parent.bottom
                  padding: 2
                  textFormat: Text.PlainText
                  text: strings.t("shot").arg(I18n.formatNumber(shotTile.number))
                  color: Color.foreground
                  Rectangle {
                    anchors.fill: parent
                    z: -1
                    radius: 3
                    color: Color.background
                  }
                }
              }
            }
          }
        }
      }

      Image {
        id: chartPreview
        visible: root.hasChart
        width: parent.width
        height: 148
        asynchronous: true
        cache: false
        fillMode: Image.PreserveAspectFit
        source: visible && card.visible ? "file://" + root.chartPath + "?v=" + root.task.id : ""
      }
      Text {
        visible: root.hasChart
        textFormat: Text.PlainText
        text: "Doble clic en la gráfica para ampliarla"
        color: Color.muted
      }
      Text {
        width: parent.width
        textFormat: Text.PlainText
        text: typeof root.task.detail === "string" && root.task.detail ? root.task.detail.slice(0, 180) : "Sin tareas en curso."
        color: Color.foreground
        wrapMode: Text.Wrap
      }
      Text {
        textFormat: Text.PlainText
        text: root.working ? "Doble clic para abrir · Alt+X para cancelar" : (root.canFollow ? "Doble clic para abrir el chat" : "")
        color: Color.muted
      }
    }

    MouseArea {
      id: grab
      anchors.fill: parent
      hoverEnabled: true
      onEntered: forceActiveFocus()
      onDoubleClicked: mouse => {
        const position = grab.mapToItem(chartPreview, mouse.x, mouse.y);
        if (root.hasChart && chartPreview.contains(position))
          chartViewer.running = true;
        else if (root.canFollow)
          root.runAction("follow");
      }
      Keys.onPressed: event => {
        if (event.key === Qt.Key_X && (event.modifiers & Qt.AltModifier) && root.task.state === "working") {
          event.accepted = true;
          root.runAction("cancel");
        }
      }
    }
  }
}
