from tunnel import LocalTunnel

if __name__ == "__main__":
    # Port can be overruled via CLI argument 
    LocalTunnel(listen_port=2222).run()
