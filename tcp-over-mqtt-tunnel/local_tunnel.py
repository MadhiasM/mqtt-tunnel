from tunnel import LocalTunnel

if __name__ == "__main__":
    # Default port 2222; change here or make it configurable via config.json/CLI.
    LocalTunnel(listen_port=2222).run()
