import socket
import json
import time
import os
import struct

port = 9000

def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('', port)
    udp_socket.bind(server_address)
    print(f'Server started. Listening on port {port}...')

    with open('format.json', 'r') as f:
        format_data = f.read()
    
    data_format = json.loads(format_data)

    try:
        while True:
            # receive data from client, buffer is 312 bytes
            data, client_address = udp_socket.recvfrom(324)
            try:
                converted_data = []
                for i in range(len(data_format)):
                    field_format = data_format[i]
                    data_size = field_format['size']
                    data_type = field_format['type']
                    data_name = field_format['name']
                    
                    converted_value = None

                    if data_type == 'int8':
                        converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True)
                    elif data_type == 'uint8':
                        converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=False)
                    elif data_type == 'int16':
                        converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True)
                    elif data_type == 'int32':
                        converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True)
                    elif data_type == 'int64':
                        converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True)
                    elif data_type == 'float':
                        converted_value = struct.unpack('f', data[i * data_size : (i + 1) * data_size])[0]
                    elif data_type.startswith('int8@'):
                        conversion = data_type.split('@')[1]
                        if conversion == 'boolean':
                            converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True) == 1
                        elif conversion == 'normalize255to1':
                            converted_value = int.from_bytes(data[i * data_size : (i + 1) * data_size], byteorder='little', signed=True) / 255.0
                    # Handle other data type conversions here

                    converted_data.append({ 'name': data_name, 'value': converted_value })

                print(json.dumps(converted_data, indent=4))

            except Exception as e:
                print(f"Error processing data: {e}")
            
            data, client_address = None, None
            os.system('cls')
            print('-------------------\n\n')

    except KeyboardInterrupt:
        print('Server stopped.')

    finally:
        udp_socket.close()

if __name__ == '__main__':
    main()
