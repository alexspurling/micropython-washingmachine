import ast
import hashlib
import os

import pyboard


def file_hashes(pyb):
    buffer = bytearray()

    def read_data(byte):
        if byte != b'\x04':
            buffer.extend(byte)

    cmd = f"""
import uos
import hashlib
import ubinascii

files = []
for f in uos.listdir('/'):
  sha = hashlib.sha256()
  with open(f, 'rb') as f2:
    sha.update(f2.read())
  files.append((f, ubinascii.hexlify(sha.digest()).decode('ascii')))
print(files)
    """
    pyb.exec_(cmd, data_consumer=read_data)
    output = buffer.decode("utf-8")
    return ast.literal_eval(output)


def file_hash(f):
    sha = hashlib.sha256()
    with open(f, 'rb') as f2:
        sha.update(f2.read())
    return sha.hexdigest()


serial_device = "/dev/ttyACM0"
source_dir = "src"

pyb = pyboard.Pyboard(serial_device)
pyb.enter_raw_repl(soft_reset=False)
file_hash_map = {f[0]: f[1] for f in file_hashes(pyb)}
for source_file in os.listdir(source_dir):
    if source_file.endswith(".py"):
        source_hash = file_hash(f"{source_dir}/{source_file}")
        if not (source_file in file_hash_map) or source_hash != file_hash_map[source_file]:
            print(f"Copying {source_dir}/{source_file}")
            pyboard.filesystem_command(pyb, ["cp", f"{source_dir}/{source_file}", ":"])
        else:
            print("File hashes match:", source_file, source_hash)
pyb.exit_raw_repl()
# Write ctrl-D to trigger a soft-reset
pyb.serial.write(b"\x04")


