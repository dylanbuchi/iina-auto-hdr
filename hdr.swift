// hdr: switch macOS HDR mode on external displays that support it.
// Usage: hdr [on|off|toggle|status]
// Prints one line per HDR-capable external display: "<displayID> <on|off> <name>"
// Uses private SkyLight functions (the same switch as System Settings > Displays > High Dynamic Range).
import CoreGraphics
import Foundation
import AppKit

let sl = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_NOW)
guard let pSup = dlsym(sl, "SLSDisplaySupportsHDRMode"),
      let pIs = dlsym(sl, "SLSDisplayIsHDRModeEnabled"),
      let pSet = dlsym(sl, "SLSDisplaySetHDRModeEnabled") else {
  FileHandle.standardError.write("hdr: this macOS version doesn't expose the HDR switch\n".data(using: .utf8)!)
  exit(1)
}
typealias BoolFn = @convention(c) (CGDirectDisplayID) -> Bool
typealias SetFn = @convention(c) (CGDirectDisplayID, Bool) -> Int32
let supports = unsafeBitCast(pSup, to: BoolFn.self)
let isOn = unsafeBitCast(pIs, to: BoolFn.self)
let setHDR = unsafeBitCast(pSet, to: SetFn.self)

func name(_ id: CGDirectDisplayID) -> String {
  NSScreen.screens.first { ($0.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?.uint32Value == id }?.localizedName ?? "display"
}

let cmd = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "status"
guard ["on", "off", "toggle", "status"].contains(cmd) else { print("usage: hdr [on|off|toggle|status]"); exit(2) }
var ids = [CGDirectDisplayID](repeating: 0, count: 16); var n: UInt32 = 0
CGGetOnlineDisplayList(16, &ids, &n)
for id in ids.prefix(Int(n)) where CGDisplayIsBuiltin(id) == 0 && supports(id) {
  if cmd != "status" {
    let want = cmd == "on" ? true : cmd == "off" ? false : !isOn(id)
    if want != isOn(id) { _ = setHDR(id, want) }
  }
  print("\(id) \(isOn(id) ? "on" : "off") \(name(id))")
}
