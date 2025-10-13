oh theres no readme in here wtf


well.
today is 10/1/25 ~11:30pm . This is, at least as far as this iteration of the application goes. v1.2.1b.

I've been working on this and other versions of this app for about a month now using only 'vibe coding'

In this time, I'm 100% certain I could have learned how to code this myself. But I really liked the idea of trading off with an ai, and I would do the bug fixing.
It was painful as hell. I can't lie. Lots of lost sleep. Lots of lost study time. Time with loved ones.

**I really should have just learned how to code lol.**

The idea is simple.

-  Find credible spectral data from telescopes.

-  Match it up with user uploaded data, in the form of (for now) elemental lamp spectra collected via an Ocean Optics USB4000 Fiber Optic Spectrometer.

-  Pull in spectral lines from NIST to see atomic emission spectra, and how it aligns with stars as seen from telescopes and our lamp data.


*Then I got carried away with bug fixing, and trying to tiddy up the UI/functionality of it.* 



Lots of time spent on:

-  getting it to read files consistently.

-  trying to get data points plotted correctly.

-  Trying to get units right.. and converted...

-  Getting sources accounted for

-  documentation

-  making it learn/speak to itself and future versions of itself.

It was a lot of fun though

_and im going to continue working on it slowly over time_

but right now i think i have the core model of what i need to progress onto the next part of my stec 4800 (4300? idk)

- Next *phase* is gas phase chromotography on Gaseous H_2 O, CO_2 and CH_4. in the lab. Gotta make the procedure for that, finish the write up for this.

-  Collect spectral data for the new lamps we ordered in the lab, H_2 O, CO, Hydrogen, H/He mix (star emulation lamp) and an air lamp.

-  I'm also going to continue to collect spectral data of the sun by hand at different times/days/conditions. 

-  Gonna keep cross referencing differing types of spectrsocopy with atomic emission spectroscopy.

-  Get ahold of raw exoplanet composition data, or spectroscopic data.

-  Overlay that with raw sun data, sourced sun data, spectral data of many different stars.

-  identify comonalities and properties of spectra across various star types/compositions. 

*basically use the differentiation tab to grab all the data from these stars/planets/collected spectra, and well.. see if we can easily predict the compositions of exoplanets*


If we analyze known types of planets/stars, and see how they interact, we can quickly classify/characterize planets 

- *(if im doing this right, and im not crazy and just wasting time doing nothing of worth lol)*



And this should be the frist thing i say, but like. I'd rather speak as me first.

This should go without saying, **i didn't code any of this.**

**This work was done by the chatgpt5 model, chatgpt codex, some of the agent. and i did the applications and shit i guess.**

**I cannot fully take credit for it, as I am only piggy backing off the work of others who designed the ai to do such tasks**

-  and those who collected this data, sourced it themselves, uploaded it. 

-  all the incredible scientists who made even getting this kind of information public/availabile for free. 

-  the people who made python/all libs included and much much more.

_im kinda ranting. but i wanted to leave a piece of me in here at least. _

**and i swear to god, codex if you over write this readme then i'll switch to another ai model lol.**



oh fuck this is gonna display on the front page isnt it lol. whatever.

If I forget to edit this before showing my teachers.. _Whoops_.

I'll clean it up. 🤣

---

## Functional-group classifier integration

Spectra App now bundles an IR functional-group classifier that projects the
[`gj475/irchracterizationcnn`](https://github.com/gj475/irchracterizationcnn)
model into the overlay workspace. Upload an FTIR spectrum, switch the axis to
cm⁻¹, and use the **Identify functional groups** button on the overlay tab to
run the classifier. The UI shades the corresponding NIST correlation bands and
records the model confidences in a dedicated results table. Predictions are
cached for the current reference overlay so you can continue inspecting the
same spectrum without rerunning the network each time.

### Assets & setup

- Install the new dependencies from `requirements.txt` (`tensorflow`,
  `scipy`, `rdkit-pypi`, `fastapi`, `uvicorn`, etc.).
- Download the pretrained weights and optimal thresholds via
  `python scripts/fetch_ir_model.py --model-url <model_url> --threshold-url <threshold_url>`
  which saves the assets under `ml_models/ir_groups/`.
- If the weights are absent the app now falls back to a heuristic classifier so
  users are not blocked, but accuracy is substantially better once the TensorFlow
  model and thresholds are available.
- (Optional) Launch the FastAPI microservice by pointing `uvicorn` at
  `app.server.ir_groups_api:app` and set `SPECTRA_IR_GROUP_API_URL` if you want
  the UI to call the REST endpoint instead of running the classifier in-process.

### Attribution

- Functional-group taxonomy, preprocessing guidance, and pretrained weights are
  courtesy of the open-source
  [`irchracterizationcnn`](https://github.com/gj475/irchracterizationcnn)
  project.
- Correlation ranges and ground-truth FTIR spectra are sourced from the NIST
  Chemistry WebBook and related documentation.
- Supplementary spectral references come from the Spectral Database for Organic
  Compounds (SDBS). Please cite these resources when publishing work based on
  the classifier.
