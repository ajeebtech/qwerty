def register(app):
    @app.slash_command("/nginx")
    def nginx_command(args, ssh, ai, display):
        if not args:
            display.status_warning("Usage: /nginx [status|reload|test]")
            return
        
        cmd_type = args[0].lower()
        if cmd_type == "status":
            ssh.run("systemctl status nginx --no-pager")
        elif cmd_type == "reload":
            ssh.run("nginx -s reload || systemctl reload nginx")
        elif cmd_type == "test":
            ssh.run("nginx -t")
        else:
            display.status_warning(f"Unknown nginx command: {cmd_type}. Supported: status, reload, test")
