# Voice Call with ChatGPT

This repository is a demo of what'd be possible if you could have ChatGPT to place a call on your behalf. This is __experimental__ and not meant to actually be used for placing calls. But it's pretty fun to play around with.

It also was built using the [Eleven Labs](https://beta.elevenlabs.io/) Voice AI API so that you could create your own voice and then have it act as the voice of ChatGPT.

## How to use

Install the dependencies:

```
pip install -r requirements.txt
```

I've included some example prompts for common scenarios where you might want a bot to place a call for you. Of course, you could also add your own. 

To run a scenario, run the following command:

```
python main.py -pf 'path/to/prompt/file.txt'
```

Replacing the path above with the path to the prompt file you want to use.

When it starts, you'll see a "Listening..." message. That's essentially the same as a phone call being picked up. You can then play the role of the receiver, ChatGPT will play the role of the caller.