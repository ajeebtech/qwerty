def register(app):
    @app.slash_command("/ssl")
    def ssl_command(args, ssh, ai, display):
        if not args:
            display.status_warning("Usage: /ssl [status|renew]")
            return
        
        cmd_type = args[0].lower()
        if cmd_type == "status":
            ssh.run("certbot certificates 2>/dev/null || stat /etc/letsencrypt/live/ 2>/dev/null || echo 'Certbot certificates not found.'")
        elif cmd_type == "renew":
            ssh.run("certbot renew")
        else:
            display.status_warning(f"Unknown ssl command: {cmd_type}. Supported: status, renew")
