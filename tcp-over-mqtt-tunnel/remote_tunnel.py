from tunnel import RemoteTunnel

if __name__ == "__main__":
    # Port can be overruled via CLI argument 
    RemoteTunnel(target_host="localhost", target_port=22).run()
