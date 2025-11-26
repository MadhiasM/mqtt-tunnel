from tunnel import RemoteTunnel

if __name__ == "__main__":
    # TODO: move into config.json if you vary it often.
    RemoteTunnel(target_host="localhost", target_port=22).run()
