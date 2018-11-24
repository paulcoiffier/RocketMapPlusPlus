# Creating an application + bot in Discord

1. First you need to go to [here](https://discordapp.com/developers/applications/) and click **Create an application**.

2. Now give your application a name and click on the **Save Changes** button. Take note of your API client credentials: **Client ID** and **Client Secret**.

![Application Name](../_static/img/auth-discord/create-app.png)

3. Click on **OAuth2** on the left and click on the **Add Redirect** button. Set your redirect URI to your externally visible hostname (`--external-hostname`), ending with `/auth_callback` - to make sure the map receives the authentication codes. Example: `https://website.com/auth_callback`

![Application Redirect URI](../_static/img/auth-discord/auth-callback.png)

4. Click on **Bot** on the left and click on the **Add Bot** button. Also click the confirmation alert **Yes, do it!**.

![Create Bot User](../_static/img/auth-discord/create-bot.png)

5. Now you can get your bot's token by using the **Click to Reveal Token** button.

![New Bot Page](../_static/img/auth-discord/bot-token.png)

6. You now have your bot's access token! Now, to invite the bot to your server we need to generate an OAuth2 URL. Don't worry about the bot being up and running for this next step. Click on OAuth2 on the left. To generate the correct OAuth2 URL, make sure that **bot** checkbox in _Scopes_ section and **Manage Roles** checkbox in _Bot Permissions_ section are checked. Click on the **Copy** button to copy the generated URL to your clipboard.

![Bot Required Permissions](../_static/img/auth-discord/bot-permissions.png)

7. Open a new tab in your browser and navigate to the URL from the previous step. You will be presented to a page that looks like this:

![Authorize Bot](../_static/img/auth-discord/bot-authorize.png)

8. Now select your server in the dropdown, then click **Authorize**.

![Authorized](../_static/img/auth-discord/bot-authorized.png)

**That's it!** Now you can start your bot and enjoy chatting!

**IMPORTANT: you should NEVER give your bot's token to anybody you do not trust, and never EVER under any circumstances push it to a public Git repository where everyone can see it.** The token gives you full access to your bot account's permissions, so if somebody gains access to it maliciously they could do any number of bad things with the bot -- this includes leaving all of its guilds (servers), spamming unfavorable links or messages in text channels, deleting messages/channels in guilds where it has moderator permissions, and other nasty stuff along those lines. Keep it a secret! 

## Compromised client secret or bot token 
If your API client secret or bot token ever does get compromised, or you suspect it has been, the very first thing you should do is [go to its Discord Apps page](https://discordapp.com/developers/applications) and generate new ones.

- Client Secret: press **click to reveal** in the _App Details_ section, then click **Generate a new secret?** and **Yes, do it!** in the confirmation dialog. This will give you a unique, brand-new client secret you must use from now on.

- Bot Token: press **click to reveal** in the _App Bot User_ section, then click **Generate a new token?** and **Yes, do it!** in the confirmation dialog. This will give you a unique, brand-new token that you can update your bot's code with.

Afterwards, take the appropriate measures to place these new credentials in a secure place where it can't be leaked or compromised again.
