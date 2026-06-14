import re

BUILTIN_HOSTERS = ["digitalocean", "hetzner", "vultr", "aws", "linode"]

HOSTER_OVERLAYS = {
    "digitalocean": (
        "DigitalOcean Profile active:\n"
        "- Default user is root or ubuntu depending on distro.\n"
        "- Firewall: both ufw (on-box) and DigitalOcean Cloud Firewall (account level) may be active.\n"
        "- Snapshots: available via doctl CLI if installed, or control panel.\n"
        "- Managed DBs: remind the user not to expose ports if using managed databases."
    ),
    "hetzner": (
        "Hetzner Profile active:\n"
        "- Default user is root.\n"
        "- Firewall: Hetzner Cloud Firewall (external) + nftables/ufw on-box.\n"
        "- Rescue mode: Hetzner rescue mode is available via the Robot/Cloud Console if the VPS is unreachable.\n"
        "- IPv6: enabled by default. Configure dual-stack if deploying apps."
    ),
    "vultr": (
        "Vultr Profile active:\n"
        "- Default user is root.\n"
        "- Firewall: Vultr Firewall Groups + ufw on-box.\n"
        "- Startup scripts: supported for reproducible deployments."
    ),
    "aws": (
        "AWS EC2 Profile active:\n"
        "- Default user varies by AMI: ubuntu, ec2-user, or admin.\n"
        "- Firewall: Security Groups (external, not visible on-box) + iptables/ufw.\n"
        "- Instance metadata is available at http://169.254.169.254.\n"
        "- IAM roles: may be attached. AWS CLI can run without keys if a role is present."
    ),
    "linode": (
        "Linode / Akamai Profile active:\n"
        "- Default user is root.\n"
        "- Firewall: Linode Cloud Firewall + ufw on-box.\n"
        "- StackScripts: available for reproducible provisioning."
    )
}

def detect_hoster(ssh) -> str | None:
    """Fingerprints remote VPS to determine provider (AWS, Hetzner, DO, Vultr, Linode)"""
    try:
        # Check sys_vendor fallback
        out_vendor, _, _ = ssh.run("cat /sys/class/dmi/id/sys_vendor", was_dry_run=False, confirm_all=False)
        out_vendor = out_vendor.lower()
        if "amazon" in out_vendor or "aws" in out_vendor:
            return "aws"
        if "hetzner" in out_vendor:
            return "hetzner"
        if "digitalocean" in out_vendor:
            return "digitalocean"
        if "linode" in out_vendor:
            return "linode"
        
        # Check product_name fallback
        out_product, _, _ = ssh.run("cat /sys/class/dmi/id/product_name", was_dry_run=False, confirm_all=False)
        out_product = out_product.lower()
        if "amazon" in out_product:
            return "aws"
        
        # Check cloud.cfg fallback
        out_cloud, _, _ = ssh.run("cat /etc/cloud/cloud.cfg 2>/dev/null", was_dry_run=False, confirm_all=False)
        out_cloud = out_cloud.lower()
        if "digitalocean" in out_cloud:
            return "digitalocean"
        if "hetzner" in out_cloud:
            return "hetzner"
        if "vultr" in out_cloud:
            return "vultr"
        if "aws" in out_cloud or "ec2" in out_cloud:
            return "aws"

        # Check metadata endpoint
        out_meta, _, _ = ssh.run("curl -s --max-time 1.5 http://169.254.169.254/metadata/v1.json 2>/dev/null || curl -s --max-time 1.5 http://169.254.169.254/metadata 2>/dev/null", was_dry_run=False, confirm_all=False)
        if out_meta:
            out_meta = out_meta.lower()
            if "digitalocean" in out_meta or "droplet" in out_meta:
                return "digitalocean"
            if "aws" in out_meta or "instance-id" in out_meta or "ami-id" in out_meta:
                return "aws"
            if "hetzner" in out_meta:
                return "hetzner"
            if "vultr" in out_meta:
                return "vultr"

    except Exception:
        pass
    
    return None

def get_hoster_overlay(hoster: str) -> str:
    hoster = hoster.strip().lower() if hoster else ""
    return HOSTER_OVERLAYS.get(hoster, "")
