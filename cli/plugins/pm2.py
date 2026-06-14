def register(app):
    @app.slash_command("/pm2")
    def pm2_command(args, ssh, ai, display):
        if not args:
            display.status_warning("Usage: /pm2 [list|restart <app>|logs <app>]")
            return
        
        cmd_type = args[0].lower()
        if cmd_type == "list":
            ssh.run("pm2 list")
        elif cmd_type == "restart":
            if len(args) < 2:
                display.status_warning("Usage: /pm2 restart <app_name>")
                return
            ssh.run(f"pm2 restart {args[1]}")
        elif cmd_type == "logs":
            if len(args) < 2:
                display.status_warning("Usage: /pm2 logs <app_name>")
                return
            # Get last 50 lines to avoid hanging
            ssh.run(f"pm2 logs {args[1]} --lines 50 --raw --no-daemon")
        else:
            display.status_warning(f"Unknown pm2 command: {cmd_type}. Supported: list, restart, logs")
