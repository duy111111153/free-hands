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
  property bool hidden: false
  property bool pinned: false
  property bool expired: false
  property int previewRefresh: 0
  property bool captureFlash: false
  readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/free-hands"
  readonly property string cameraSession: /^camera-[a-z0-9_]{8}$/.test(task.camera_session || "") ? task.camera_session : ""
  readonly property int frameNumber: Number.isInteger(task.camera_frame) && task.camera_frame > 0 && task.camera_frame <= 100 ? task.camera_frame : 0
  readonly property int shotCount: Number.isInteger(task.camera_shots) && task.camera_shots >= 0 && task.camera_shots <= 3 ? task.camera_shots : 0
  readonly property bool working: task.state === "working" || task.state === "cancelling"
  readonly property bool dockToLeft: task.corner === "top-left"
  readonly property bool canFollow: /^[0-9a-fA-F-]{36}$/.test(task.thread_id || "")
  readonly property string executable: Quickshell.env("HOME") + "/Work/free-hands/free-hands"
  // Keep the target monitor independent from PanelWindow.screen to avoid a
  // visible/screen binding loop while Quickshell reloads local plugins.
  readonly property var monitor: Quickshell.screens[0]

  function toggleCard() {
    if (pinned || !hidden) {
      hidden = true;
      pinned = false;
    } else {
      hidden = false;
      pinned = true;
    }
  }

  function runAction(action) {
    if (actionProc.running || !/^[a-f0-9]{32}$/.test(task.id || ""))
      return;
    actionProc.command = action === "cancel" ? [executable, "cancel", "--task-id", task.id] : [executable, "follow", task.id];
    actionProc.running = true;
  }

  Process {
    id: actionProc
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
        const previousSession = root.cameraSession;
        const previousCount = root.shotCount;
        root.task = next;
        if (root.cameraSession !== "" && root.cameraSession === previousSession && root.shotCount > previousCount) {
          root.captureFlash = true;
          flashTimer.restart();
        }
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
    id: flashTimer
    interval: 125
    onTriggered: root.captureFlash = false
  }
  Timer {
    id: expiry
    interval: 8500
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
    visible: !root.hidden && (root.pinned || root.working || (!root.expired && ["done", "cancelled", "error"].includes(root.task.state)))
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
      color: Color.background
      border.color: root.working ? Color.accent : Color.muted
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
        onClicked: {
          root.hidden = true;
          root.pinned = false;
        }
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
      Row {
        id: visualPreviews
        width: parent.width
        spacing: 6
        visible: root.cameraSession !== "" || root.task.screen_active === true

        Rectangle {
          visible: root.cameraSession !== ""
          width: screenPreview.visible ? (visualPreviews.width - visualPreviews.spacing) / 2 : visualPreviews.width
          height: screenPreview.visible ? 116 : 160
          color: Color.background
          clip: true

          Image {
            id: cameraPreview
            anchors.fill: parent
            asynchronous: true
            retainWhileLoading: true
            fillMode: Image.PreserveAspectFit
            cache: false
            sourceSize.width: 448
            source: card.visible && root.cameraSession !== "" && root.frameNumber ? "file://" + root.runtimeDir + "/" + root.cameraSession + "/preview-" + (root.frameNumber % 3) + ".jpg?v=" + root.frameNumber : ""
          }

          Text {
            anchors.centerIn: parent
            visible: cameraPreview.status !== Image.Ready
            textFormat: Text.PlainText
            text: "Abriendo webcam…"
            color: Color.muted
          }

          Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 6
            width: cameraLabel.implicitWidth + 12
            height: cameraLabel.implicitHeight + 6
            radius: 4
            color: Color.background
            Text {
              id: cameraLabel
              anchors.centerIn: parent
              textFormat: Text.PlainText
              text: root.task.camera_active === true ? "Webcam en vivo" : "Cámara cerrada"
              color: Color.foreground
            }
          }

          Rectangle {
            anchors.fill: parent
            color: "white"
            opacity: root.captureFlash ? 0.62 : 0
            visible: opacity > 0
            Behavior on opacity {
              enabled: !root.captureFlash
              NumberAnimation {
                duration: Style.duration(100)
                easing.type: Style.easeOut
              }
            }
          }
        }

        Image {
          id: screenPreview
          visible: root.task.screen_active === true
          width: root.cameraSession !== "" ? (visualPreviews.width - visualPreviews.spacing) / 2 : visualPreviews.width
          height: 116
          fillMode: Image.PreserveAspectFit
          asynchronous: true
          retainWhileLoading: true
          cache: false
          sourceSize.width: 448
          source: card.visible && visible ? "file://" + root.runtimeDir + "/screen-preview.jpg?v=" + root.previewRefresh : ""
        }
      }

      Row {
        id: shotStrip
        width: parent.width
        spacing: 6
        visible: root.cameraSession !== ""
        Repeater {
          model: 3
          Rectangle {
            required property int index
            width: (shotStrip.width - shotStrip.spacing * 2) / 3
            height: 67
            radius: 4
            color: Color.background
            border.color: root.shotCount === index + 1 && root.captureFlash ? Color.accent : Color.muted
            Image {
              anchors.fill: parent
              anchors.margins: 2
              asynchronous: true
              fillMode: Image.PreserveAspectFit
              cache: false
              sourceSize.width: 160
              source: card.visible && root.cameraSession !== "" && root.shotCount > index ? "file://" + root.runtimeDir + "/" + root.cameraSession + "/shot-" + (index + 1) + ".jpg" : ""
            }
            Rectangle {
              anchors.horizontalCenter: parent.horizontalCenter
              anchors.bottom: parent.bottom
              anchors.bottomMargin: 4
              width: shotLabel.implicitWidth + 10
              height: shotLabel.implicitHeight + 4
              radius: 4
              color: Color.background
              Text {
                id: shotLabel
                anchors.centerIn: parent
                textFormat: Text.PlainText
                text: "Toma " + (index + 1)
                color: Color.foreground
              }
            }
          }
        }
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

    Timer {
      interval: 600
      repeat: true
      running: card.visible && screenPreview.visible
      onTriggered: root.previewRefresh++
    }

    MouseArea {
      id: grab
      anchors.fill: parent
      hoverEnabled: true
      onEntered: forceActiveFocus()
      onDoubleClicked: if (root.canFollow)
        root.runAction("follow")
      Keys.onPressed: event => {
        if (event.key === Qt.Key_X && (event.modifiers & Qt.AltModifier) && root.task.state === "working") {
          event.accepted = true;
          root.runAction("cancel");
        }
      }
    }
  }
}
