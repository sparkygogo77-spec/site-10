import json, struct, sys, glob
for path in sys.argv[1:]:
    b = open(path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); rest = b[20 + n:]
    for m in j.get("materials", []):
        if "ring" in m.get("name", "").lower():
            m["pbrMetallicRoughness"]["baseColorFactor"] = [0.05, 0.75, 0.3, 1]
            m["emissiveFactor"] = [0.1, 1.0, 0.4]
            m.setdefault("extensions", {})["KHR_materials_emissive_strength"] = {"emissiveStrength": 0.8}
    js = json.dumps(j, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
    body = struct.pack("<II", len(js), 0x4E4F534A) + js + rest
    open(path, "wb").write(b[:8] + struct.pack("<I", 12 + len(body)) + body)
