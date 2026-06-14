def register(app):
    @app.slash_command("/docker")
    def docker_command(args, ssh, ai, display):
        if not args:
            display.status_warning("Usage: /docker [ps|restart <container>|logs <container>]")
            return
        
        cmd_type = args[0].lower()
        if cmd_type == "ps":
            ssh.run("docker ps -a")
        elif cmd_type == "restart":
            if len(args) < 2:
                display.status_warning("Usage: /docker restart <container_name_or_id>")
                return
            ssh.run(f"docker restart {args[1]}")
        elif cmd_type == "logs":
            if len(args) < 2:
                display.status_warning("Usage: /docker logs <container_name_or_id>")
                return
            ssh.run(f"docker logs --tail 50 {args[1]}")
        else:
            display.status_warning(f"Unknown docker command: {cmd_type}. Supported: ps, restart, logs")
