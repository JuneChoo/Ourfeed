# Setting Ourfeed up for your family (or small group)

Ourfeed isn't a cloud product, there's no "ourfeed.com" you sign up on.
Someone in your group runs it on one computer (the **host**), and everyone
else connects to that one instance. This doc is written for that first
conversation with non-technical family members: what to tell them, and what
to send them.

*(中文版见 [family-setup.zh.md](family-setup.zh.md))*

## The two roles

- **Host**: whoever's computer/server runs `python ourfeed.py`. Usually
  whoever set this up (you). Only needs to be online when others want to use
  it; a phone or a machine that sleeps constantly doesn't work well as a host.
- **Everyone else**: just needs a browser and, per the network step below,
  Tailscale installed once.

## Step 1: Host sets up Ourfeed

Follow the [README quick start](../README.md#quick-start). At the end of
this step you can open `http://localhost:8731` on the host machine itself
and see the login page. Register the first account, it automatically
becomes the admin.

## Step 2: Get everyone on the same private network

This is the part that trips people up, so it's worth explaining why it's
needed. Ourfeed isn't exposed to the public internet, and that's a feature,
not a bug: nobody can stumble onto your family's feed from a Google search
or a port scan. But that also means a family member's phone, on a different
WiFi network entirely, can't just type in an address and reach it. You need
a private network that follows your devices around, and that's what
[Tailscale](https://tailscale.com) is for.

**Why Tailscale specifically:** it's free for personal/family use (up to 100
devices on the free tier), takes about 2 minutes to install, and doesn't
require you to configure your router, open ports, or get a static IP. Every
device that installs it and logs into the same Tailscale network can reach
every other device on that network, wherever they physically are, whether
that's home WiFi, cellular data, or a hotel in another country.

1. Host installs Tailscale on the machine running Ourfeed, and signs in
   (Tailscale accounts are free, Google/GitHub/Microsoft login works).
2. Host runs `tailscale ip` to get that machine's Tailscale IP (looks like
   `100.x.x.x`). Ourfeed will be reachable at `http://<that-ip>:8731`.
3. Each family member installs the Tailscale app on their phone/laptop and
   either joins the host's Tailscale network directly, or, so family members
   don't get full access to *all* the host's devices, the host uses
   [Tailscale's "Share" feature](https://tailscale.com/kb/1084/sharing) to
   share just the one device running Ourfeed with each family member's own
   Tailscale account.

## Step 3: Host generates invite codes

Once logged in as admin, go to `/admin.html` and click "Generate invite
code." Each code works once. Send one code per person you're inviting.

## Step 4: What to send your family member

Copy-paste and adapt this. It's written for someone who has never heard the
words "self-hosted" or "Tailscale" before:

> Hey, I set up a private little version of Twitter/X just for us, called
> Ourfeed. Nobody outside our family can see it, it's not on the public
> internet at all.
>
> To connect:
> 1. Install **Tailscale** on your phone (it's free: [tailscale.com](https://tailscale.com)). Sign in with [Google/whatever the host is using].
> 2. I'll add your account so you can reach my computer through it. You'll get a notification, just accept it.
> 3. Once that's done, open this in your phone's browser: `http://<tailscale-ip>:8731`
> 4. Tap "Register with an invite code," use this code: `<code>`, and pick any username and password.
>
> That's it. Bookmark the page or save it to your home screen and it works
> like any app after that.

## Troubleshooting

- **"It says can't reach the server"**: the host's computer is probably
  asleep or Ourfeed isn't running. Ourfeed only works while the host machine
  is on and the `python ourfeed.py` process is running (or set up as an
  always-on service, see the README's deployment note).
- **"Tailscale is installed but the page won't load"**: check that both
  devices show as connected in the Tailscale admin console
  (login.tailscale.com), and that you're using the Tailscale IP (`100.x.x.x`),
  not `localhost` or the host's regular home WiFi IP.
- **Forgot password**: there's no self-serve reset. Ask the admin (whoever's
  running Ourfeed) to reset it directly in the database.

## Alternatives to Tailscale

If your family is always on the same home WiFi (e.g. one household), you
don't need Tailscale at all, just use the host's local network IP
(`http://192.168.x.x:8731`) directly. Tailscale only matters once someone
needs to reach it from outside that network. If you're comfortable with
reverse proxies, domains, and TLS certificates, exposing Ourfeed behind
something like Caddy or nginx with your own domain is also an option, but
for a first setup with non-technical family members, Tailscale is by far
the least explaining you'll have to do.
