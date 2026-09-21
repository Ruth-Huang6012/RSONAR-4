import socket
import os
# https://stackoverflow.com/questions/59691694/sending-multiple-files-through-a-tcp-socket/59692611#59692611

s = socket.socket()
s.bind(('', 5001))
s.listen()

folderpath = r'/Test'
while True:
    client, address = s.accept()
    print(f'{address} connected')

    # client socket and makefile wrapper will be closed when with exits.
    with client, client.makefile('rb') as clientfile:
        while True:
            folder = clientfile.readline()
            if not folder:  # When client closes connection folder == b''
                break
            folder = folder.strip().decode()
            no_files = int(clientfile.readline())
            print(f'Receiving folder: {folder} ({no_files} files)')
            os.makedirs(folderpath, exist_ok=True)
            for i in range(no_files):
                filename = clientfile.readline().strip().decode()
                filesize = int(clientfile.readline())
                data = clientfile.read(filesize)
                print(f'Receiving file: {filename} ({filesize} bytes)')
                with open(os.path.join(folderpath, filename), 'wb') as f:
                    f.write(data)
