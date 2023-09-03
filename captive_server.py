import socket
import json
import struct
import requests

captive_port = 9000
webservice_port = 5000

def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('', captive_port)
    server_ip = socket.gethostbyname(socket.gethostname())
    udp_socket.bind(server_address)
    print(f'Server started. Listening on {server_ip}:{captive_port}...')

    with open('format.json', 'r') as f:
        format_data = f.read()

    data_format = json.loads(format_data)
    try:
        while True:
            data, client_address = udp_socket.recvfrom(324)
            try:
                converted_data = []
                for entry in data_format:
                    if entry['type'] == 'uint8@boolean':
                        converted_data.append(bool(struct.unpack('B', data[:entry['size']])[0]))
                    elif entry['type'] == 'int64':
                        converted_data.append(struct.unpack('q', data[:entry['size']])[0])
                    elif entry['type'] == 'float':
                        converted_data.append(struct.unpack('f', data[:entry['size']])[0])
                    elif entry['type'] == 'int32':
                        converted_data.append(struct.unpack('i', data[:entry['size']])[0])
                    elif entry['type'] == 'int16':
                        converted_data.append(struct.unpack('h', data[:entry['size']])[0])
                    elif entry['type'] == 'int8':
                        converted_data.append(struct.unpack('b', data[:entry['size']])[0])
                    else:
                        print(f"Error: Unknown type {entry['type']}")
                    data = data[entry['size']:]

                    converted_data.append({
                        'name': entry['name'],
                        'value': converted_data[-1],
                        'type': entry['type'],
                        'size': entry['size']
                    })

                # print the converted data
                # for i in range(len(converted_data)):
                #    print(f"{data_format[i]['name']}: {converted_data[i]}")

                # send the converted data to the web server
                requests.post('http://localhost:{port}/data'.format(port=webservice_port), json=converted_data)

            except Exception as e:
                print(f"Error processing data: {e}")

            data, client_address = None, None
            print('-------------------\n\n')

    except KeyboardInterrupt:
        print('Server stopped.')

    finally:
        udp_socket.close()


if __name__ == '__main__':
    main()
