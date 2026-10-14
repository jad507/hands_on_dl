# Gold coding sheet (BLIND)

Code these blocks **before** looking at any model output. The companion
`gold_sample_KEY.json` holds the model votes and the strata; opening it
first does not corrupt the data, it corrupts you, and nothing downstream
can detect that.

## What to record, per item

1. **`public_comment`** -- is the TARGET block a member of the public
   addressing the body? `yes` / `no` / `unsure`.
   Council members, staff, and procedural speech are `no`. A block that
   fuses a public comment with something else is `unsure` -- say so in
   the note, because unit boundaries are part of what is being studied.
2. If `yes`, score each of the four themes **0.0 to 1.0**:
   `municipally_managed_resources`, `municipal_process`,
   `health_and_well_being`, `power_dynamics_and_inequality`.
   Definitions and anchor quotes: `downloads/data_center_comment_themes.md`.
3. **`note`** -- anything that made the judgement hard. These are worth more
   than the labels; they are what a reliability statistic cannot record.

Context blocks are shown in grey brackets **for orientation only**.
Do not code them.

Write answers in `gold_coding.csv` (a template is written alongside this
file), keyed by `item`.

---

## Item 1

*City Council Meeting - July 8, 2025*  |  speaker `SPEAKER_11`  |  1024.75s-1193.71s  |  511 words

<sub>[context before, speaker SPEAKER_12: up to it am i good now thank you you got it okay uh yeah i really don't have anything to add to that what i i'm truly grateful to accept this proclamation but t ...]</sub>

**TARGET --**

> I'd also like to take a minute here just for a few remarks on on the city's parks and recreation and this resolution I'd like to recognize the city's expansion of programming in Yule Park and bins or Yule Plaza and bins Park weekly programming scheduled for Yule bins includes a kids fitness class happening Tuesdays from 6 to 7 p.m. a pop-up beer garden brought to you by South County brewing Wednesday nights from 5 to 8 p.m. and a high-intensity interval training boot camp brought to you by LA Fitness on Thursdays from 5 to 7 p.m. You can find more information about programming. The city will be hosting in Yule Plaza and Binns Park at yuleplaza.com or by following the Yule Plaza and Binns Park page on social media. I'd also like to recognize many staff at both the Lancaster Rec and the city's Bureau of Parks and Public Property for all the work they do into not just maintaining the city's 16 parks but continually working to make these parks even better with more to offer for residents just in the last year or so the city has invested significantly in longs park with new art installations as well as the wetlands at longs park project which won a best urban bmp in the bay area award a bubba award from the chesapeake stormwater network as well as a governor's award for environmental excellence from the pa department of environmental protection as many of you know longs park continues to host the annual summer music series as well series of concerts happening every sunday night from now until the last concert on august 17th you can learn more about the summer music series at longspark.org additionally this council last year as you all know approved the park's master plan and the city continues to gear up for upcoming improvements to the joe jackson tot lot south end park yule gantz park and reservoir park so just to wrap this up i just want to say that our city parks serve an important purpose for residents since many residents don't have much in the way of yards i've of ...

<sub>[context after, speaker SPEAKER_08: you very much councillor hirsch um jack thank you for being here tonight i think you are you're underselling uh the benefit of the lancaster rack in the communi ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 2

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_07`  |  12183.39s-12234.88s  |  149 words

<sub>[context before, speaker SPEAKER_20: a second um this is your committee but it was the parliamentarian advice i would i mean if we're]</sub>

**TARGET --**

> making a motion to to table um you know i i i i i will state again that i do not support this for the reasons that were aforementioned that it creates a misalignment between the community's expectations and reality and that that's kind of the issue at hand and that's that's that's kind of emblematic to me of the conversations i've been having of people who saw this and said well i don't like that there's three police officers on it and i don't like that it doesn't have teeth and there is no such you know as the mayor stated there's not there's no example of that in pennsylvania so i i i don't support it and i'm i like i'm tabling it as in like i'm done with the conversation um and if that means we have to table it until january 2026 that's my motion

<sub>[context after, speaker SPEAKER_26: a second so to be clear because my question with the tabling is you know when are we tabling this till you know what steps are going to be taken by the chair of ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 3

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_02`  |  1720.19s-1731.71s  |  20 words

<sub>[context before, speaker SPEAKER_09: zone that's that's not what i understood and that's even what i even called ben about about]</sub>

**TARGET --**

> the loading zone i think we talked about the fact was going to be a loading zone on lemon street

<sub>[context after, speaker SPEAKER_09: and that is why well i sent you pictures of the loading zone on print street has anybody looked at]</sub>

`public_comment:` ____   `note:` ____

---

## Item 4

*City Council Meeting - March 11, 2025*  |  speaker `SPEAKER_36`  |  1958.57s-2087.82s  |  398 words

<sub>[context before, speaker SPEAKER_29: Good evening.]</sub>

**TARGET --**

> Evening. My name is Daryl Lagacy. I live in the 100 block of North Mary. Thank you for allowing me to address the council. here to talk about the interaction that happened that we're probably all here for people say that you don't know what happened before the video started they say the kids were doing wheelies they were going the wrong way down the street maybe yeah maybe they were it doesn't justify having someone two to three times the weight of that kid with his knee on his back face down not resisting crying for help like that just when you look at that I don't know how you can see that and say oh yeah that's the right response I hear a lot of people complain about cancel culture they say they're afraid to be cancelled for saying the wrong thing or doing the wrong thing when I don't see our police worried about being cancelled I don't see police officers worried about what it looks like when they kneel on someone saying they can't breathe we've done this for five years really for a hundred years and I don't see them being worried when they push someone who's recording them which happened twice in that video it's unacceptable so I'm calling for four things one release the names of all police officers involved in that situation release all the body cam footage leading up to and during the encounter reinstate the community police working group and require de-escalation training for all officers to everyone here and everyone in the city i'm asking you to record every single public police encounter from now on especially those with people of color i realize i'm a white person i am privileged i mostly don't have to worry about this i don't want to be here speaking tonight but I feel like I have to be it's your constitutional right to record police if it is in public so here people say oh you complain about the police and then you're the first one to go running to them when you need something yeah that's the job okay that's their job no one made them become police off ...

<sub>[context after, speaker SPEAKER_29: Our next speaker is our next speaker.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 5

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_08`  |  1403.47s-1418.7s  |  35 words

<sub>[context before, speaker SPEAKER_04: composition of what's going on throughout the year yes we certainly do]</sub>

**TARGET --**

> that as well um but that driveway as you probably know is really probably fits four to five cars because you keep a lane open for obviously emergency services so it's sort of an extension

<sub>[context after, speaker SPEAKER_02: of the driveway and you know very critical i think your question was from the park garage not from]</sub>

`public_comment:` ____   `note:` ____

---

## Item 6

*City Council Meeting - May 27, 2025*  |  speaker `SPEAKER_05`  |  1937.22s-1946.84s  |  30 words

<sub>[context before, speaker SPEAKER_12: Well, in that case, in a situation like this, I have my friends, I have my family, but at the end of the day, I was raised by a Marine, and it's all about the g ...]</sub>

**TARGET --**

> council president and thank you theodore for your uh willingness to serve and answering our questions this evening how do you believe that integrity and honesty and elected officials can

<sub>[context after, speaker SPEAKER_12: build trust in the community I think it's everything I I think if you see you know the people that you voted for if you see them engaging in things that are tha ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 7

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_20`  |  6616.12s-6642.3s  |  55 words

<sub>[context before, speaker SPEAKER_30: 20 21 of them altogether so in essence this ordinance makes it um makes the requirements to serve on these boards more rigorous and also we have more of those c ...]</sub>

**TARGET --**

> thank you my only question is it's great to hear that we have multiple who are certified now in the future there's only one person who's certified and would the director still appoint somebody who wasn't certified or would it still remain only those who are certified to serve that that's a great question thank

<sub>[context after, speaker SPEAKER_15: you uh in our case right now we have uh three people on staff who could fulfill that role if for some reason in the future we don't have anyone who has the prop ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 8

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_14`  |  8480.62s-8508.95s  |  72 words

<sub>[context before, speaker SPEAKER_11: they're acting in good faith yeah I appreciate the question and this is where we were trying to stretch into some territory to ensure that a developer this deve ...]</sub>

**TARGET --**

> also renewable as we've seen the three billion dollar purchase of hydro power by Google on the Susquehanna River over the next 20 years so that I think that there's a combination of factors and that are at play here in terms of the the power utilization or the power source and also pushing up against the limits of what we can accomplish in a zoning text amendment thank you and I

<sub>[context after, speaker SPEAKER_26: appreciate the work being done by your department and by city staff and I would just hope that we continue to think about ways to protect city residents]</sub>

`public_comment:` ____   `note:` ____

---

## Item 9

*Traffic Commission Meeting - November 11, 2025*  |  speaker `UNKNOWN`  |  1740.64s-1744.02s  |  13 words

<sub>[context before, speaker SPEAKER_00: trucks with 53 foot trailers that you would typically see on the interstate we need to accommodate those turning movements at the intersection which requires qu ...]</sub>

**TARGET --**

> at this intersection we're proposing a curb bump out to kind of protect

<sub>[context after, speaker SPEAKER_00: bicyclists at the intersection and also shorten the pedestrian crossing distance as well throughout the project we're narrowing the travel lanes to pretty much  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 10

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_28`  |  10527.94s-10559.38s  |  77 words

<sub>[context before, speaker SPEAKER_27: why is this it's not expedited well i mean it's so typically a land development wouldn't go through]</sub>

**TARGET --**

> the public hearing process um this process is outlined in the zoning ordinance but it's following a planned residential development requirement that's provided for in the mpc um i can't speak to the reasoning behind this this addition being in the zoning ordinance um it is in my opinion a little bit unique but that the zoning ordinance is what dictates those time frames and those are based off of the mpc regulations for planned residential development

<sub>[context after, speaker SPEAKER_25: and so it's an extra step and so like yeah well i mean you would ultimately do the same thing that]</sub>

`public_comment:` ____   `note:` ____

---

## Item 11

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_25`  |  11267.14s-11281.17s  |  15 words

<sub>[context before, speaker SPEAKER_11: because September 3rd you're dealing with Labor Day right before that and I]</sub>

**TARGET --**

> don't see it being advantageous of this month you can I just think that the

<sub>[context after, speaker SPEAKER_28: Sycamore Ridge is a pretty intricate plan and just tiny people like I said]</sub>

`public_comment:` ____   `note:` ____

---

## Item 12

*City Council Meeting - September 9, 2025*  |  speaker `SPEAKER_03`  |  3093.86s-3143.05s  |  106 words

<sub>[context before, speaker SPEAKER_08: leave some hard copies of this presentation for any counselors or community members that would like i left it with mr harris so counselors mayor sirachi preside ...]</sub>

**TARGET --**

> questions thank you so much for your presentation this evening um i do have a question off the bat so having seen you know these presentations for now several years it seems sort of anecdotally if i'm remembering correctly that your participation has gone up since your new location could someone uh speak to the way that things have changed like day to day in the library since it moved to its new location the good the bad the the positive what how much how much would you say it has increased since the new location opened don't be shy one of the things we've seen

<sub>[context after, speaker SPEAKER_12: for sure is people just coming and enjoying the space it's a lot more open to people who are there to just relax and read or work with their ipads or their lapt ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 13

*City Council Ethics Code Work Session - November 6, 2025*  |  speaker `UNKNOWN`  |  2662.52s-2689.14s  |  84 words

<sub>[context before, speaker SPEAKER_00: we get to a hearing to try and give an opportunity for resolution ultimately once a hearing is held that's where counsel would be assigned the code sets forth t ...]</sub>

**TARGET --**

> investigator and presenting the facts origin I mean they can be appointed by the solicitor but if it's problematic so if my office is at issue i would not appoint them the ethics commission would do that directly again you know for them to have to search out attorneys would be a challenge we're hoping that it wouldn't be my office and that i'd be able to assist in finding counsel who are unbiased and impartial and don't have any conflicts as required but

<sub>[context after, speaker SPEAKER_00: obviously if i am the subject or it would be problematic for me to be involved even in the the appointment then my me my success or anybody in my office then ob ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 14

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_15`  |  8734.6s-8806.43s  |  207 words

<sub>[context before, speaker SPEAKER_22: THANK YOU. I'LL TAKE QUESTIONS AND]</sub>

**TARGET --**

> COMMENTS FROM THE PUBLIC. CAN YOU FIRST START WITH YOUR name and your block of residence my name is matthew barden i'm on the 800 block of north prince thank you we can see this this document tacitly acknowledges the numerous potential downsides of this facility to the community energy and water use and pollution chief among them to all acknowledge the glaring lack of detail around the proposed limits of this facility at this time what i'm failing to see is the benefit to the city at large or any individual residents of lancaster this kind of facility creates no meaningful number of community jobs provides no necessary or desired local service. Any argued tax benefits to the community would ignore the long-standing tradition in this country of corporate entities evading their responsible tax burdens to the local community, and even ignoring that, pale in comparison to the litany of medical issues that these facilities have already proven to lead to in the short term, and that doesn't even account the currently unproven long-term environmental and health impacts. There's no amount of financial benefit offered by these data centers that could conceivably offset the corresponding detriment to public health and welfare. It's very easy to find

<sub>[context after, speaker SPEAKER_24: stories about communities that have suffered because of these data centers but i've yet to]</sub>

`public_comment:` ____   `note:` ____

---

## Item 15

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_05`  |  2551.01s-2564.47s  |  43 words

<sub>[context before, speaker SPEAKER_04: conversation if he wants to proceed would you I'm sorry I'm not understanding]</sub>

**TARGET --**

> Would it meet your needs to have a loading zone that's further south than what your initial request was? I understand your initial request was one that's directly south of what's now the handicapped parking spot. And the recommendation was to deny that.

<sub>[context after, speaker SPEAKER_09: That would be the ideal one because if you want to take a poll of all the…]</sub>

`public_comment:` ____   `note:` ____

---

## Item 16

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_17`  |  14549.07s-14581.85s  |  87 words

<sub>[context before, speaker SPEAKER_22: We do understand the position to mitigate it, whatever the concerns may be.]</sub>

**TARGET --**

> Could we table this motion and collect more information from the city to understand how this could really affect other parcels? I know that you said that there's a number of other parcels that could potentially do this. I would be interested to know where those parcels are located and what the opportunities are on them for that, um and then revisit this conversation i think that's my preferred method to proceed without having the process start all over again i will just say that pushes us

<sub>[context after, speaker SPEAKER_10: i'm curious if we can use the transportation the transportation constraints as like it's by right but if there's a for example no frontage accessible by the roa ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 17

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_04`  |  3172.76s-3178.28s  |  20 words

<sub>[context before, speaker SPEAKER_21: you'll have to explain to me why the steepness of the property relates to the number of cross]</sub>

**TARGET --**

> sections you want to see i'm also not an engineer so i don't know that i can provide feedback on

<sub>[context after, speaker SPEAKER_21: that as far as being incomplete there are concerns with over the past year as]</sub>

`public_comment:` ____   `note:` ____

---

## Item 18

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_31`  |  2836.75s-2935.21s  |  226 words

<sub>[context before, speaker SPEAKER_00: Thank you.]</sub>

**TARGET --**

> Terry McLean, 123 South Christian Street. yeah okay I would just good evening I would just like to remind you that our beloved Longs Park is next to the Harrisburg pie I can't believe no one's talking about this that place will be unusable unusable after this is put in the second thing is the other one over on Greenfield Road is right across the street from Conestoga Pines swimming pool and park what the heck cut this out not only that but the noise will from what I'm reading is going to be so loud that it's almost like you're gonna blanket the area because you have one on the east one on the west and everything it's only three miles across Lancaster I've really like I walked across it we're gonna hear this it's gonna be loud for everyone I just would like you to revisit this at least I mean if the one on greenfield road has to come through at least get something in place sometime soon here because we're not they're not going to stop with these two as easy it is here as easy it is it's been for them to come in here they'll be doing more and josh shapiro is going to make it easy and the republicans in the state uh state house are going to make

<sub>[context after, speaker SPEAKER_12: it easy too so and we won't get taxes from it if it's from the state thank you uh hi]</sub>

`public_comment:` ____   `note:` ____

---

## Item 19

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_24`  |  9835.12s-9857.2s  |  67 words

<sub>[context before, speaker SPEAKER_09: something you should yeah i also agree with that and i think it's super important to have that um just because like i saw the note like on uh page 15 that these ...]</sub>

**TARGET --**

> legally binding in itself correct it runs with their deed and that stormwater om agreement that is executed with the sale of the property it runs with the deed for the individual property owners and the ones following that that take the ownership they have responsibilities and i think that we could help facilitate i don't lauren you had yeah no i was just saying that the

<sub>[context after, speaker SPEAKER_22: city probably has something that could be handed out we have a ton of stormwater that would be]</sub>

`public_comment:` ____   `note:` ____

---

## Item 20

*City Council Committee Meeting - November 3, 2025*  |  speaker `UNKNOWN`  |  7390.32s-7394.64s  |  15 words

<sub>[context before, speaker SPEAKER_00: oh there's a self storage you know somebody could build a huge self storage]</sub>

**TARGET --**

> facility there and we don't you know our zoning doesn't match that is that kind

<sub>[context after, speaker SPEAKER_00: of the intention that's exactly right but we're primarily thinking about would be a lot consolidation because that's something that anyone could do by right]</sub>

`public_comment:` ____   `note:` ____

---

## Item 21

*City Council Committee Meeting - September 16, 2025*  |  speaker `SPEAKER_06`  |  3282.62s-3293.18s  |  28 words

<sub>[context before, speaker SPEAKER_00: You could but I wouldn't recommend it because those could change over time. One of the things that one of the things that you want to be conscious of in draftin ...]</sub>

**TARGET --**

> question is actually being questioned by a community member that wanted to know why the numbers of members are not there. So that's that's something I would probably

<sub>[context after, speaker SPEAKER_04: agree with Mr. Hamburger that the Web site would be an easier way for community members to access that information. That's a very good idea. And also and knowin ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 22

*Planning Commission*  |  speaker `SPEAKER_01`  |  1725.87s-1787.53s  |  172 words

<sub>[context before, speaker SPEAKER_09: um yeah we got a lot of time so i'll figure i'll just kind of informally be like let's talk a little bit about the comp plan stuff um i was curious if it would  ...]</sub>

**TARGET --**

> guys feel is appropriate because i'd like to see a reduction so i can work on getting you the gis file um i would maybe caution you not to go outside of the realms of a committee when we go through the zoning process because all of that would be explored in the committee portion of it um obviously having ideas of what you want to what you think should happen would be good i do believe the comp plan includes a reduction in the number of zoning districts and kind of consolidation so we are looking at that at the next planning commission meeting very loud the next planning commission meeting i'm going to kind of present the timeline that we're looking for to go through the zoning ordinance process update process and i can also provide a implementation plan that we have for 2025 and we're working on that right now um for the comp plan so okay like the high priority yeah betsy logan i'm the planning bureau chief

<sub>[context after, speaker SPEAKER_09: so thank you um no i'm just one person on the body but i i am definitely the type of person who likes to throw ideas out there for just general consumption uh a ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 23

*City Council Budget Hearing - November 18, 2025*  |  speaker `UNKNOWN`  |  3287.92s-3297.76s  |  31 words

<sub>[context before, speaker SPEAKER_00: mr. president public comment Amos thoughts who is one or block of South]</sub>

**TARGET --**

> Arch Street I'm thinking back to the last budget hearing and particularly looking or thinking about the police budget um and and i might be wrong about this so you may

<sub>[context after, speaker SPEAKER_00: have to uh remind me uh so i think in the in the police budget they were trying to get up to the 128 staff members and we're at 110 i think it's about 105 right ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 24

*City Council Meeting - May 27, 2025*  |  speaker `SPEAKER_17`  |  1699.6s-1713.85s  |  37 words

<sub>[context before, speaker SPEAKER_13: important now more than ever absolutely thank you theodore counselor craig thank you council]</sub>

**TARGET --**

> president and hello good evening it's very nice to see you again could you tell us about a time when you had an ethical dilemma and how you solved it yeah so um let me think here

<sub>[context after, speaker SPEAKER_12: I would say, actually, it came down, my previous job, I worked at another library before this one, I was out at E-Town, and we had a lot of books that were prop ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 25

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_10`  |  3798.08s-3832.32s  |  76 words

<sub>[context before, speaker SPEAKER_04: had, you had brought part of this to our attention. I think you had reached out to see if there were residents who were willing to come and speak. Yes,]</sub>

**TARGET --**

> but I didn't. I would have to schedule for her to come in to see because she does work, so she's not able to come around this time. But she did bring it to my attention. And the elderlies that are living on the opposite direction that the neighbor question was, they're elderly, and they had to get to garages in order to avoid the constant trying to get parking, because those tow trucks are there.

<sub>[context after, speaker SPEAKER_04: it seems like it's more like it's an enforcement issue um which means that please correct me if this is not the appropriate strategy that in the short term sinc ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 26

*Planning Commission Meeting - September 3, 2025*  |  speaker `SPEAKER_09`  |  4257.86s-4266.95s  |  23 words

<sub>[context before, speaker SPEAKER_11: text amendment i'll second motion on the floor in a second ready for the question discussion all in favor let it known by saying aye aye aye aye aye aye opposed ...]</sub>

**TARGET --**

> so like so do you mind if i i don't want i don't want to get away from my head um i appreciate

<sub>[context after, speaker SPEAKER_08: what you said ms sufert about you know essentially community cooperation what we can do with more foresight um i there's two points to make and what i have to s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 27

*City Council Meeting - August 12, 2025*  |  speaker `SPEAKER_24`  |  2312.0s-2395.98s  |  236 words

<sub>[context before, speaker SPEAKER_10: i'm on the 800 block of third street i was here last week for the planning commission meeting and spoke about some similar things and i heard a lot of people wh ...]</sub>

**TARGET --**

> our next speaker mr harris is dan weigel good evening uh dan weigel uh clarendon drive um as you may have noticed there's a petition going around um there's a petition going around in our community about the data center we have hundreds of signatures on it it's been in the news obviously this is a big deal to our community I'd like to take my time tonight first to read the petition to you all as AI companies to send on Pennsylvania to build data centers local governments need to make a choice stand up to big tech or sell out their constituents in Lancaster City we're facing the construction of two AI data centers that have gone under the radar until recently setting aside the negative effects of the global AI race these data centers will cause price hikes for utilities lower the supply of water and electricity and create harmful new air and noise pollution across the country many communities that have become sites for data centers have been forced to deal with rolling blackouts and low water pressure or watching their utility bills become more and more expensive we don't want that to happen in Lancaster City we call on Lancaster City government to do the following one City Council must request from the Planning Commission an ordinance that covers the zoning of data centers and rescind the zoning officers decision to

<sub>[context after, speaker SPEAKER_24: and storage they are not warehouses to mayor Sirachi and City Council must work with the public to pass a plan that insulates Lancaster residents from the negat ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 28

*City Council Meeting - April 8, 2025*  |  speaker `SPEAKER_21`  |  3723.4s-3740.45s  |  17 words

<sub>[context before, speaker SPEAKER_19: Any additional council comments on the resolution? And I'll just remind everyone that there is a procedure for requesting a flag to be flown at City Hall. Those ...]</sub>

**TARGET --**

> Mr. Mayor, ah I say resolution number 25 2025 mr. Harris a resolution of the Council of

<sub>[context after, speaker SPEAKER_20: the City of Lancaster approving an amended capital project list to be funded by the proceeds of the City of Lancaster general obligation bonds]</sub>

`public_comment:` ____   `note:` ____

---

## Item 29

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  13806.0s-13877.82s  |  122 words

<sub>[context before, speaker SPEAKER_16: like allowing making it easier to do this kind of thing and even in the cm districts i think that]</sub>

**TARGET --**

> they should be permissible but i think that they should kind of be like last resorts and i i can understand your point about the zoning hearing board having a huge load um but hopefully we can reduce some of that load with the overall comprehensive plan updates that we need to make i would take great reservation with approving self-storage by right in these zones but i do agree with eliminating it in the r3 and r4 any further comment i think the commission should consider a motion to maybe table this so that more like individual retrospection can be done about it but i can't make that motion so that's why i'm saying that how's the city what's the city's

<sub>[context after, speaker SPEAKER_04: stance um we went through several iterations of this draft ordinance to get it to the point where it's at and so at this time the city's in support of it so i g ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 30

*City Council Committee Meeting - February 3, 2025*  |  speaker `SPEAKER_07`  |  1942.8s-1966.69s  |  54 words

<sub>[context before, speaker SPEAKER_00: excuse me the other thing I wanted to add is that we did it wouldn't I believe it was in the December presentation the November presentation we had our my deput ...]</sub>

**TARGET --**

> to be my last question in regards to um these projects do we have anything included that was already added in regards to the grants is there any grants that we had added into this because i'm just trying to figure out what the difference between the debt and also the minus the grants

<sub>[context after, speaker SPEAKER_04: yeah um so the one that i will point out is the vision zero work um so that is uh most of that that i believe it's 2.1 of the 2.7 million um is actually for mat ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 31

*City Council Meeting - October 28, 2025*  |  speaker `SPEAKER_00`  |  3754.69s-3806.27s  |  130 words

<sub>[context before, speaker UNKNOWN: that question and um and like he said about the trash and I'm going to meet with Steve about that]</sub>

**TARGET --**

> afterwards him and I have a meeting set up thank you thank you good evening uh good evening honorable managers of council thank you my name is Bill Simonson I live on the 800 block of role with Javanu like many citizens here tonight and many more who could not make it I come here dismayed to hear that we are getting AI data centers built in our community and the process in which they were approved to be here I think it is the history of America is such that the rich win and often the poor are powerless and Lancaster City to me I'm losing hope in it it seems to be a city that favors the developers the bankers now the tech companies and their wealthy lawyers

<sub>[context after, speaker UNKNOWN: well i would ask tonight that city council unfortunately the mayor is not here but that we become a city that favors the little person that favors the mom waiti ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 32

*City Council Special Meeting - November 20, 2025*  |  speaker `UNKNOWN`  |  3351.77s-3359.27s  |  15 words

<sub>[context before, speaker SPEAKER_00: it. And Chris, did you ever want to add anything there? Thanks, Barry. Mostly, I just wanted to talk about these particular elements as a group. I think Barry c ...]</sub>

**TARGET --**

> the community benefits agreement and how that works in tandem with the proposed zoning amendment.

<sub>[context after, speaker SPEAKER_00: don't want to muddy the waters and talk about the zoning amendment too much right now but I think it's important to give credit to the work of staff and City Co ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 33

*City Council Committee Meeting - July 15, 2025*  |  speaker `SPEAKER_00`  |  667.41s-708.45s  |  139 words

<sub>[context before, speaker SPEAKER_03: as a reminder what you have before you is only about half of the admin code the other half will will be presented to you in August. This section deals mostly an ...]</sub>

**TARGET --**

> about you know i kind of thought and i racked my brain as i looked at it again because i was like i'm not sure i mean maybe it doesn't make much of a difference but i thought you know um having the budget activity like the what on the far left then the due date and then who's responsible for it would just kind of read better like like just the way it reads now it kind of um like the date isn't as relevant to people necessarily as like the what and so if you start with the what and then say like so preparation of budget when's it due it's due on before the last meeting of council and um the resp the responsible parties um i mean i might be splitting hairs so i just

<sub>[context after, speaker SPEAKER_03: now when i looked when i looked at it when it came in i thought it was a good suggestion i've actually already implemented in draft format so i agree with you c ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 34

*City Council Committee Meeting - November 3, 2025*  |  speaker `UNKNOWN`  |  1110.78s-1122.46s  |  31 words

<sub>[context before, speaker SPEAKER_00: thankful to say that i'm only seeing general trends of keeping expenses below budget at this point even if some of those individual lines are a bit higher and f ...]</sub>

**TARGET --**

> notes about the four enterprise funds i'm including debt payments in all of these points just because i wanted to show kind of the true costs even though they aren't included

<sub>[context after, speaker SPEAKER_00: in the september financials so the stormwater fund with the debt expenses included is running about 72 or 72 percent of expenses um budgeted currently we're exp ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 35

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  4305.78s-4342.16s  |  107 words

<sub>[context before, speaker SPEAKER_15: those nuanced uh you can't quite put your finger on it but i think it's a um it was a vision and an idea that we had hey can we make this work and can we embed  ...]</sub>

**TARGET --**

> you had said that the wooded cliffside is unusable i disagree with that personally in fact i think that using cliff sides can become a remarkably great use for ecological design the insulation the ground provides to the structures you're building within um so i i don't really have a question there i just want to state that for the record that i i think that that doesn't hold water uh the cliff sides are usable it's just you've made a choice to focus on a different type of of design um i'll stop for a second if anybody else has questions a number of questions regarding

<sub>[context after, speaker SPEAKER_17: the affordability of this project you have called this project an affordable project a number of times um 350 000 starter home is not an affordable starter home ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 36

*City Council Committee Meeting - August 11, 2025*  |  speaker `SPEAKER_02`  |  2123.88s-2151.56s  |  82 words

<sub>[context before, speaker SPEAKER_11: would expect to see that then in the next report wonderful thank you thank you councilor arroyo]</sub>

**TARGET --**

> and thank you director campbell this report was very helpful my question was regarding the unfilled positions and the vacancies are we planning to keep those vacancies throughout the rest of the fiscal year and given that we are seeing revenues a little bit ahead of what were anticipated is there any um is there any discussions about bringing some of those positions back um to kind of uh alleviate some of the other staff pressures sure yeah none of the positions

<sub>[context after, speaker SPEAKER_08: are um permanently vacant at this point these would be vacancies that somebody has left and we you know take a couple months to fill again so it's this uh kind  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 37

*Home Rule Transition Committee Meeting - July 29, 2025*  |  speaker `SPEAKER_03`  |  1118.21s-1150.45s  |  94 words

<sub>[context before, speaker SPEAKER_00: Yep, okay, thank you.]</sub>

**TARGET --**

> And to add, yeah, to add, in my council comments post of when we have these meetings, I do make council aware of what we've been talking about in these meetings and the public aware and when our next scheduled meeting is. So I've been trying to, as the representative of council to this body, I've been trying to take this back to council at the next meeting after we meet each time and also let us know and let them know and the public know when the next scheduled transition committee meeting is.

<sub>[context after, speaker SPEAKER_00: Okay, that's great. So, and the reason I, I mean, there's three things on my mind related to this, you know, and the reason I asked to include it on the agenda. ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 38

*City Council Committee Meeting - August 11, 2025*  |  speaker `SPEAKER_11`  |  3228.82s-3258.89s  |  37 words

<sub>[context before, speaker SPEAKER_04: underway thank you and if i could just add to that to say that the former use of lsc was consuming more water than the proposed new use and so i just want to ma ...]</sub>

**TARGET --**

> questions uh from the public works committee or council as a whole any questions or comments from the public and if you don't mind if you could just state your name and block her residence as well

<sub>[context after, speaker SPEAKER_10: for the meeting record all right taylor raymond 500 block of saint joseph street um i just wanted some clarification on the reduced timelines you said from uh 1 ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 39

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_20`  |  9340.89s-9347.16s  |  17 words

<sub>[context before, speaker SPEAKER_28: the current cost would be to develop the park i do not have a current estimate that estimate was from 2023 is and director campbell's shaking his head yes so 20 ...]</sub>

**TARGET --**

> thank you um and that concludes my question counselors we have a motion on the table from

<sub>[context after, speaker SPEAKER_30: counselor ds is there a second hearing none that motion fails um are there any additional comments]</sub>

`public_comment:` ____   `note:` ____

---

## Item 40

*City Council Meeting - April 29, 2025*  |  speaker `SPEAKER_15`  |  1859.56s-1866.32s  |  33 words

<sub>[context before, speaker SPEAKER_17: have order in the room thank you good evening miss Dixon good evening I just]</sub>

**TARGET --**

> wanted to start off by saying it's an honor to be in this room this is my first time being here after the chamber has been named after my grandfather nelson polite senior

<sub>[context after, speaker SPEAKER_14: and i live on his in his property our polite estate in the 500 block of north street]</sub>

`public_comment:` ____   `note:` ____

---

## Item 41

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_00`  |  1458.49s-1507.88s  |  137 words

<sub>[context before, speaker SPEAKER_02: sorachi um any questions from the public this would be in regards to either resolution 25 or 26.]</sub>

**TARGET --**

> starting bird and street once again i'm going to ask council why they do not put this information up on the screen that you're showing we spend a lot of money updating city this city council chambers with technology and yet you're talking about things that we're not able to see it's not available on the website at this time and it needs to be put out to the public one of the reasons when i was on the home rule and suggested even about the reports was that so the public would but have more information, not just the council members. So again, I'm asking council, hoping to get an answer, why this is not presented to the public so we can see what she's referring to or what anyone's referring to when they're presenting something.

<sub>[context after, speaker SPEAKER_01: Thank you. Tony D'Astra, 700 Block New Holland Avenue. I want to echo what Darlene's saying. Municipal government is where we as the people supposed to understa ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 42

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_03`  |  2613.56s-2615.14s  |  7 words

<sub>[context before, speaker SPEAKER_09: I would rather bring it back to where it was for 41 years.]</sub>

**TARGET --**

> That's not an option at this point.

<sub>[context after, speaker SPEAKER_09: Pardon me?]</sub>

`public_comment:` ____   `note:` ____

---

## Item 43

*Traffic Commission Meeting - November 11, 2025*  |  speaker `SPEAKER_00`  |  2840.58s-2862.79s  |  94 words

<sub>[context before, speaker UNKNOWN: miko um and pamela had reached out to us about uh about the issue and i just recently a couple weeks prior heard from my staff just talking about how they've ob ...]</sub>

**TARGET --**

> or chestnut or you know they're all kind of treated like three ways it kind of even if it's a one way even i feel like i can kind of see sort of see i think that's everybody and then sometimes somebody's cruising at 45 miles an hour and it's hard to you know hard to see that car but uh but yeah we'd love to come to some sort of resolution that makes it safer very good thank you very very much is anyone else wanting to speak on this item from the

<sub>[context after, speaker UNKNOWN: public in the introduction to the issue yes please and again your name and block of residence hey I'm Steve Farina I live on the 400 block of Lancaster Avenue s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 44

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_26`  |  11254.19s-11280.16s  |  70 words

<sub>[context before, speaker SPEAKER_21: unfortunately i have a fever so i'm a little bit out of it today but um i will i can forward that to everyone in city council and if you have a question tony go ...]</sub>

**TARGET --**

> finished oh you're not finished and and lastly i would just you know like to note that you know without any robust input from the solicitor's office from the chief of police and given that we're going to have a new chief of police a new administration and a new public safety commission um i don't think this resolution is appropriate and that's my final comment i would also like

<sub>[context after, speaker SPEAKER_07: to i guess ask the question if like if the administration's position is that it's not legal i would want to know what the what the reasoning or like um you know ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 45

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  5959.92s-5965.28s  |  19 words

<sub>[context before, speaker UNKNOWN: a little nervous about that you know if you have kids who are getting ready to graduate college i mean these people are going on tv elon and others essentially  ...]</sub>

**TARGET --**

> to lead to 800 permanent jobs i don't know about anybody else but that doesn't sound like a great

<sub>[context after, speaker UNKNOWN: investment to me and you know listen i understand we're in a small city it's hard there are decisions]</sub>

`public_comment:` ____   `note:` ____

---

## Item 46

*City Council Special Meeting - November 20, 2025*  |  speaker `UNKNOWN`  |  9171.36s-9176.4s  |  15 words

<sub>[context before, speaker SPEAKER_00: and i just want to ask the people in here tonight that are supporting this project would they want to live have the data center in their backyard would they be  ...]</sub>

**TARGET --**

> knowing there are all kinds of air particles floating around the air and poisonous uh

<sub>[context after, speaker SPEAKER_00: not nitro oxides or whatever floating around i don't think you want to do that do you want to shop at Wegmans with all this pollution and water pollution out th ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 47

*City Council Meeting - May 27, 2025*  |  speaker `SPEAKER_12`  |  1841.33s-1878.46s  |  120 words

<sub>[context before, speaker SPEAKER_00: madam president and thank you for your willingness to serve and how would you ensure that the Commission's decisions are applied fairly and consistently under t ...]</sub>

**TARGET --**

> Commission comes in I'm hoping like any good Commission that there are people from multiple different backgrounds a very diverse Commission of all different ages as well so then when we're looking at you know any policy we can engage with that from a lot of different perspectives and i feel like that is how you make sure that something is fair for all is that all different eyes have to be on it i would just be one i'm a 35 year old white guy but i'm hoping that the entire committee is made up of a lot of different people so that we can have multiple sets of eyes on there to make sure that these decisions that

<sub>[context after, speaker SPEAKER_04: these policies are fully ethical good thank you that's all right thank you council president Thank you, Theodore, for your willingness to serve. How would you h ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 48

*Planning Commission Meeting - September 3, 2025*  |  speaker `SPEAKER_05`  |  1593.08s-1599.42s  |  15 words

<sub>[context before, speaker SPEAKER_01: is for um conditional approval so the first one is the preliminary plan submission procedure that just allows us to obviously proceed with the plan which was de ...]</sub>

**TARGET --**

> those were the requirements that we're asking where we thought and again this city satisfied

<sub>[context after, speaker SPEAKER_07: with where this is proceeding yes again um the they were at the shade i will i will speak for terry and say that they actually went to the shade tree commission ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 49

*Planning Commission Meeting - September 3, 2025*  |  speaker `SPEAKER_12`  |  4378.31s-4433.78s  |  86 words

<sub>[context before, speaker SPEAKER_08: what you said ms sufert about you know essentially community cooperation what we can do with more foresight um i there's two points to make and what i have to s ...]</sub>

**TARGET --**

> understand the background information to that decision i want to echo commissioner dastra and maybe request like can we just have a standing agenda item where it's an update on where we're at with updating the zoning code because i feel like we go kind of months without hearing and i think it's really important for us that to be front and center for this body um are these consulting firms local national then do we have a sense of the timeline for the upper update

<sub>[context after, speaker SPEAKER_05: is there a goal that the city has in order to get some of this um you know work underway from]</sub>

`public_comment:` ____   `note:` ____

---

## Item 50

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_09`  |  5552.59s-5569.09s  |  33 words

<sub>[context before, speaker SPEAKER_08: do we know where that may be they're my questions a couple of those questions if you want me to um and i'm going to invite you so first part we don't know if we ...]</sub>

**TARGET --**

> i can't remember i'm sorry we're assuming it's going to be between 12 and 15 million dollars what all told total at the value of the dollars in the respective years and so

<sub>[context after, speaker SPEAKER_08: that that is why we we don't know if we're even going to get any grant funding or if they're only going to have a lot of appropriate funds for a loan but we're  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 51

*City Council Meeting - April 8, 2025*  |  speaker `SPEAKER_07`  |  4090.38s-4167.06s  |  209 words

<sub>[context before, speaker SPEAKER_19: the money for resolution 26 we're talking about right projects in the water fund right that that]</sub>

**TARGET --**

> just got completed in now in 2024 and we found out that this money is left over yes projects do take several years right and now okay let me ask you a little bit differently right i don't think you're following me so in 2018 we had projects that were we took out bonds for the sewer and those projects got completed when that we now have this money left over they only got completed in 2025 right okay well this one's 2022 the one before was 2018 so the projects that got completed they just got completed in 2025 some of them yes some of these that were funded and you have a list of them which ones they were and how much was left because maybe that would make more sense to me yes because that's kind of like what I'm asking because we're borrowing more bond money and we're having bond money left and we're paying interest on this stuff you could send it to me you don't have to be if you will if you will you know that to me that will be fine I would like to see that and know what projects were completed and how much was left from each project

<sub>[context after, speaker SPEAKER_19: thank you thank you and I do think I don't see director Campbell either actually but there's your Tina Campbell I believe you had presented these with uh could  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 52

*City Council Budget Hearing - October 21, 2025*  |  speaker `UNKNOWN`  |  5610.71s-5618.47s  |  21 words

<sub>[context before, speaker SPEAKER_00: we were budgeted for 4.9 million in cped but apparently our projected expenses for this year]</sub>

**TARGET --**

> is 5.4 million um what was that extra expense due to and how was it offset and was any of that

<sub>[context after, speaker SPEAKER_00: offset coming from reserves can you ask that question again tim because i just want to make]</sub>

`public_comment:` ____   `note:` ____

---

## Item 53

*Home Rule Transition Committee Meeting - October 29, 2025*  |  speaker `UNKNOWN`  |  1656.38s-1661.36s  |  15 words

<sub>[context before, speaker SPEAKER_00: far more limited section and there there there will be some educational]</sub>

**TARGET --**

> components as John can tell you there's there's a little as they looked at these

<sub>[context after, speaker SPEAKER_00: there's some a lot of its definitional and understanding of process and understanding what legally you can and can't do with elected officials so]</sub>

`public_comment:` ____   `note:` ____

---

## Item 54

*City Council Meeting - April 29, 2025*  |  speaker `SPEAKER_17`  |  2103.86s-2108.1s  |  18 words

<sub>[context before, speaker SPEAKER_15: i came this evening to make a few remarks regarding the calls for the resignation of councilwoman janet diaz i have known janet and worked with her for eight ye ...]</sub>

**TARGET --**

> others were given thank you i've given everybody about 20 seconds of leeway in this meeting i didn't

<sub>[context after, speaker SPEAKER_15: get that same leeway as other individuals but thank you and i appreciate the opportunity to]</sub>

`public_comment:` ____   `note:` ____

---

## Item 55

*City Council Committee Meeting - March 3, 2025*  |  speaker `SPEAKER_06`  |  4176.38s-4229.97s  |  95 words

<sub>[context before, speaker SPEAKER_07: in kind of two different ways uh the first one is process uh especially since i started i've been working with um various people within the city to make sure th ...]</sub>

**TARGET --**

> good way any other question or comment from in regards to replacing some of trees do you have like specific trees that you might have found that they're disease that need removal is there any issues I mean I know one particular one that has not been removed and it's causing especially when the wind is really blustery it's it actually damaged someone's car and the neighborhood is concerns I'm curious about other you know what what exactly plans you have to remove to remove these disease trees yeah so with the processes I talked

<sub>[context after, speaker SPEAKER_07: about we have definitely made some improvements again over the last couple months so that if we have someone with a tree that is problematic we can more quickly ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 56

*Traffic Commission Meeting - November 11, 2025*  |  speaker `SPEAKER_00`  |  4214.86s-4238.87s  |  28 words

<sub>[context before, speaker UNKNOWN: oncoming traffic at times so our request is to limit parking if possible along the curb during certain hours of the day for our arrival and pickup of the studen ...]</sub>

**TARGET --**

> to add something to this I believe there had been some discussion about this before on site during a pickup time yeah they are the buses there's numerous

<sub>[context after, speaker UNKNOWN: buses that pick up children at this I think just allocating that curb space stirring and the besides enforcement the only key change would be making markings on ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 57

*City Council Committee Meeting - May 5, 2025*  |  speaker `SPEAKER_06`  |  2010.03s-2027.95s  |  19 words

<sub>[context before, speaker SPEAKER_07: times times before and um i understand that it's a new land development that needs all the criteria to move forward yep so with that i would ask are there any q ...]</sub>

**TARGET --**

> any questions from the public jose rivera honey block of corn my question is are we getting a new

<sub>[context after, speaker SPEAKER_11: water station you know because that whole thing is like only 1800s for that particular um well yes all the tainted water and everything what they'll do is they' ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 58

*City Council Meeting - April 29, 2025*  |  speaker `SPEAKER_01`  |  5324.27s-5453.49s  |  204 words

<sub>[context before, speaker SPEAKER_12: Not that I'm scared of you. My name is Ivan Acosta-Velez. I apologize for the young lady that said about that thing. Mr. Acosta, please adjust for camera. I mea ...]</sub>

**TARGET --**

> know how many times i have come here and told you guys that we need some upgrading at crystal park it hasn't been done we are going to open up the summer the west crystal volunteers are opening up the summer with mother's day i cannot secure safety in my neighborhood if the sockets are sticking out i mean they i could go on you need pictures or just come over so they had four homicides in lancaster most of those uh shootings has been happening and i don't accept that that and that was nothing like that these officers present in the neighborhood where they're at because they surely not they're not i stood at that park for 12 hours not one police officer passed by that missing a camera in that park i want that camera if all the other parks could have a camera we want a camera not the first time i'm asking for this we already paid for the flag post six hundred dollars out of our pocket fine that says the west crystal volunteers on it we want it i will keep coming back and walking to city hall i don't want to hear mine are there any

<sub>[context after, speaker SPEAKER_17: additional comments for this evening's meeting are there any additional comments for this evening's meeting that would be the time and just as a reminder please ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 59

*City Council Meeting - November 11, 2025*  |  speaker `UNKNOWN`  |  1979.63s-1985.31s  |  12 words

<sub>[context before, speaker SPEAKER_00: the invasion of their sovereign nation, condemning gun violence and legislative inaction, and most recently calling for a ceasefire in Gaza. of these issues wer ...]</sub>

**TARGET --**

> residents and that stability and consistency in funding and programming alleviates unnecessary

<sub>[context after, speaker SPEAKER_00: chaos and uncertainty i ask that lancaster city council consider adopting a new resolution calling on state and federal elected officials to pass budgets on tim ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 60

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  1043.29s-1055.92s  |  14 words

<sub>[context before, speaker UNKNOWN: that property. LPE being the first one and Greenfield being the second. So we have three parties we haven't heard about before that were formed by the party you ...]</sub>

**TARGET --**

> entities to hold what is anticipated to be three buildings. You've heard much discussion

<sub>[context after, speaker UNKNOWN: over the past months about environmental performance commitments. This agreement]</sub>

`public_comment:` ____   `note:` ____

---

## Item 61

*City Council Committee Meeting - February 3, 2025*  |  speaker `SPEAKER_01`  |  3631.16s-3639.98s  |  20 words

<sub>[context before, speaker SPEAKER_07: is is that including some of the shelters does any of that funding go to any of the local shelters]</sub>

**TARGET --**

> that we have good question the only funding that i saw that went to the shelters was from 2021 that

<sub>[context after, speaker SPEAKER_03: was part of the esg allocation so homeless shelters and service for homeless individuals is out is funded through the emergency solutions grant or esg funding f ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 62

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_02`  |  9417.2s-9427.34s  |  31 words

<sub>[context before, speaker SPEAKER_16: yeah would counsel still have to approve the methodology if there was a property]</sub>

**TARGET --**

> that the city wanted to sell or is that to the administration to determine which route they want to go to sell the property I it is my understanding and I

<sub>[context after, speaker SPEAKER_08: have to actually go back and check I have to read it again because I read it a day ago and I'm just not sure that I'm a hundred dollars but what I think is that ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 63

*City Council Committee Meeting - June 2, 2025*  |  speaker `SPEAKER_06`  |  4862.58s-4885.22s  |  68 words

<sub>[context before, speaker SPEAKER_15: be happy to if there are specific sections that people are particularly interested in we we can certainly work to address those particular areas but as it relat ...]</sub>

**TARGET --**

> anything additional from council yeah thank you kelts president my only question comment i guess would be more of a comment is uh you know other than reading and getting more familiar with the charter how could we make sure that this body stays on pace with these meetings and not try to rewrite the charter in a working session well i guess that's going to be hopefully

<sub>[context after, speaker SPEAKER_08: uh some guidance from me um and being able to point you to where the charter already controls something um and then just to focus as a group on um where the goa ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 64

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_22`  |  10461.23s-10498.43s  |  94 words

<sub>[context before, speaker SPEAKER_28: um the deadline for the initial public hearing would be the um 26 i believe of september that's the 60-day time period the discussion can be continued up to 60  ...]</sub>

**TARGET --**

> ordinance and they're essentially creating an entire neighborhood but they just want to be able to make sure that they can create it the way they want to and so in order to do that they have to follow a certain extra set of regulations and so again it was really this is really more so just like to raise your awareness that things will be coming through it will move like fairly quickly um because of the requirements of the ordinance but you you do need to make a motion to set the

<sub>[context after, speaker SPEAKER_28: public hearing date and then authorization to advertise for september 17th is it the 17th that's the date and yeah that would be yeah correct um that's our reco ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 65

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_04`  |  2042.99s-2050.78s  |  18 words

<sub>[context before, speaker SPEAKER_09: So you're putting the loading zone that people use on Lemon Street so when the purveyors that go to the Belvedere, they have to cross two intersections]</sub>

**TARGET --**

> now. Well, it's to be put in a location that tries to serve as many businesses as possible.

<sub>[context after, speaker SPEAKER_09: There's no business on Lemon Street. There's a lady that does hair, and there's a store. That's the only business that's on Lemon Street.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 66

*City Council Committee Meeting - November 3, 2025*  |  speaker `UNKNOWN`  |  3403.34s-3416.32s  |  34 words

<sub>[context before, speaker SPEAKER_00: The debt service will be will have no budgetary impact to the current projections, right?]</sub>

**TARGET --**

> Thank you. Thank You councillor mid Councillors, I think thank you vice president And I think councillor Arroyo was kind of thinking sort of along the lines. I was thinking just curious mainly for

<sub>[context after, speaker SPEAKER_00: other pen best financings do they encourage the 30-year repayment schedule or is that something we have optionality and is this just like the best timetable for ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 67

*City Council Meeting - November 11, 2025*  |  speaker `SPEAKER_00`  |  4817.72s-4843.17s  |  52 words

<sub>[context before, speaker UNKNOWN: through so much like homelessness shelter it's an enormous amount of issues that we are dealing]</sub>

**TARGET --**

> with in a community that or that two specific organizations brought to the light and stated that it could be used for usage for the community for the people for the taxpayers it could there was presentations presented and it was overlooked okay i just feel that in all reality what is

<sub>[context after, speaker UNKNOWN: compass's goal do you know miss craig can you share an email with me so you can at least let me know compass real estate's goal since you mentioned that well i' ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 68

*City Council Committee Meeting - July 15, 2025*  |  speaker `SPEAKER_03`  |  951.32s-987.91s  |  118 words

<sub>[context before, speaker SPEAKER_08: seeing article 4 as salaries of elected officials but are you looking at are you]</sub>

**TARGET --**

> looking at the admin code or the Charter I'm sorry I'm looking at the admin code right so that the Charter it's article 4 this keep in mind remember what tab yeah remember remember and this is for the public too this is this is sort of just to remember that the real Bible is the Charter that's the part that we can't change it's already been done it's been approved by the electors of the city of Lancaster and you that is that is sort of the law that we live by so the Charter is already determined through the government study process what the qualifications for the controller are what the job responsibilities are okay I

<sub>[context after, speaker SPEAKER_08: thank you for that I was I was looking at the wrong tab I appreciate that I see what we're looking and I don't I don't have anything further in this section of  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 69

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_17`  |  15108.94s-15115.5s  |  18 words

<sub>[context before, speaker SPEAKER_09: have a motion on the floor and a second and for the discussion i'm so sorry i'm just confused]</sub>

**TARGET --**

> why are we lessening the acreage don't we want to increase the acreage the lessening of the acreage

<sub>[context after, speaker SPEAKER_19: will make it apply to less lots less lots i was thinking so by going from instead of it being three to seven acres it being three to five it will include less l ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 70

*City Council Meeting - March 11, 2025*  |  speaker `SPEAKER_29`  |  7235.22s-7237.36s  |  12 words

<sub>[context before, speaker SPEAKER_42: Okay, good. I don't really talk in the microphones all day so I'm going to try and make this as streamlined as possible.]</sub>

**TARGET --**

> If you could just begin with your name and block of residence.

<sub>[context after, speaker SPEAKER_42: Yep. My name is Roe Potter. i'm on the 600 block of south franklin street i wasn't really sure how that worked until i got up here i come here tonight not fully ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 71

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_28`  |  9123.83s-9260.06s  |  271 words

<sub>[context before, speaker SPEAKER_30: thank you council diaz i want to clarify if you're making a motion at this time yes ma'am there's a motion on the table to table the resolution council craig yo ...]</sub>

**TARGET --**

> we exhausted all the possibilities to the rear of the parcel and there for a variety of reasons the inability to provide safe egress so we have spent you know at least 18 months trying to work through this um uh to come to some resolution in which we would be able to uh implement a park uh in in that particular spot i will also just say that um you know the the conversation is uh and i and i appreciate counselor diaz's um motion to table what i will say is that overwhelmingly in the course of our comprehensive plan in which we talked to 14 000 people across the city housing was the number one priority it came through loud and clear it is why council put 10 million dollars into using arpa funds to invest in affordable housing it is why we have spent more than three and a half million dollars uh last year uh and have renovated more than two 200 properties chris 200 properties south of king related to critical repair and lead remediation we we know that we need housing i believe that council has been solidly behind the administration in the work that we have been doing to support affordable housing and i also understand that this is a really it's a narrow one-way street uh in between two major thoroughfares culleton park and south end park are nearish by but you have to cross prince street to get there i get i i understand i am trying uh to get to a outcome that is meeting another need in this neighborhood

<sub>[context after, speaker SPEAKER_20: which is for affordable housing counselor uh this is a quick question um i know that it was quoted that the land development cost to build the park would be aro ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 72

*City Council Ethics Code Work Session - November 6, 2025*  |  speaker `UNKNOWN`  |  1927.03s-1930.69s  |  12 words

<sub>[context before, speaker SPEAKER_00: ask for it if it's relevant to I'm an investigation and they can get it from the city clerk and that the city clerk should be providing them with a list annuall ...]</sub>

**TARGET --**

> which is wrongful acts and whistleblower protection and while we talk about

<sub>[context after, speaker SPEAKER_00: about wrongful acts we're talking about a wrongful complaint so complaints filed when there's no real basis for doing so without any real facts those should be  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 73

*City Council Meeting - April 8, 2025*  |  speaker `SPEAKER_14`  |  7377.08s-7388.99s  |  34 words

<sub>[context before, speaker SPEAKER_19: chair because she don't belong there i would like to have a longer conversation about this but diana's just speaking generalities that i know it's very difficul ...]</sub>

**TARGET --**

> say much more but that speaks to the people watching on live to really really pay attention of who we're putting in these seats that we can't remove once they get there thank you

<sub>[context after, speaker SPEAKER_07: was a good statement as we have these council members sitting here and we continue to come whether it's a police issue a trash issue what are we going to do i m ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 74

*City Council Meeting - August 12, 2025*  |  speaker `SPEAKER_11`  |  2607.14s-2612.95s  |  7 words

<sub>[context before, speaker SPEAKER_07: Our next speaker is Jo Ellen Wisnowski.]</sub>

**TARGET --**

> Good evening. Good evening, everyone. Thank you.

<sub>[context after, speaker SPEAKER_17: Thank you all for being here, especially our council and mayor, and for all your service to our community. We appreciate everything you do and for being here. I ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 75

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  4662.56s-4717.24s  |  144 words

<sub>[context before, speaker UNKNOWN: fact that many of the environmental performance commitments were given to]</sub>

**TARGET --**

> Council almost a month ago and because they are in my mind primary to this discussion and I appreciate that the specific environmental and quality of life concerns that that we wish to prioritize have been prioritized in this process so thank you for that and thank you for the level of detail in explaining them as well I do want to go back to the economic development fund director Delphs if you could speak to the makeup of the committee that would guide that work at the Community Foundation level who who guides that work president vacate thank you for the question I realized we already spent a lot of time on so much detail and I did skip skip over a little bit of detail so it gives me an opportunity to come back here and just speak a little bit about

<sub>[context after, speaker UNKNOWN: at a high level the purpose of the fund and really what we thought about in creating this fund is wanting to ensure that these that the funds are used to promot ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 76

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_13`  |  3257.78s-3372.31s  |  320 words

<sub>[context before, speaker SPEAKER_19: in the 100 north block of plum street um i'm just adding my voice into the several that just spoke that i am against the data center i've lived here for five ye ...]</sub>

**TARGET --**

> shauna yorty i live on the 800 block of third street i don't have any uh numbers or um data points or talking points or notes and i don't know any facts except that i can't eat money and i can't breathe money and nobody else here can and i have a lot of feelings and i have a lot of questions and it's not my job to answer those questions it's y'all's job to figure that out that's why i'm over here and not over there and so the questions that i have are um have been echoed by some of the folks here but i really am concerned about the air and everybody talked about a lot of really important stuff and we talked about um boosting the power grid so that i can handle all the nonsense with the power grid like what are we doing about the particulates that are coming from the data center when we already have such a poor air quality in leicester county already what i want to know is like how many people are living in leicester city with chronic illness how many people are living in leicester city with allergies how many people are living in Lancaster city with asthma how many people elderly people and little kids are living in Lancaster that are going to be exponentially affected with their health and like what are we doing to boost the health care in Lancaster to provide health care for these people who aren't going to be able to breathe once this data center comes in because we already can hardly breathe already it's going to be massive the change and so what's going to happen to all of these people who can't breathe all of us that's my biggest question and that's my biggest concern I think thank you thank you Daniel Collins I live on West New Street

<sub>[context after, speaker SPEAKER_05: I don't have too much new to say I just want to kind of echo what everyone else has already said I obviously have concerns about air and water quality and usage ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 77

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_11`  |  8516.69s-8539.54s  |  52 words

<sub>[context before, speaker SPEAKER_26: appreciate the work being done by your department and by city staff and I would just hope that we continue to think about ways to protect city residents]</sub>

**TARGET --**

> against vague good faith effort definitions yep i we we agree and uh that is there to require that there's planning and there's thinking um but we are continuing to push on the issue of renewable as the mayor mentioned i i think that's very important are there any further questions from

<sub>[context after, speaker SPEAKER_07: council as a whole councilor hirsch uh thank you director delfts um kind of a question kind of a comment and it might come across as odd but I know for me and a ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 78

*City Council Committee Meeting - July 15, 2025*  |  speaker `SPEAKER_03`  |  1803.84s-1805.94s  |  7 words

<sub>[context before, speaker SPEAKER_08: But it will be finished before we would approve?]</sub>

**TARGET --**

> That's the goal. The admin code. Okay.

<sub>[context after, speaker SPEAKER_08: So it will be a part of what this body votes to approve.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 79

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  9250.7s-9262.36s  |  32 words

<sub>[context before, speaker UNKNOWN: EDC Lancaster County, the county's lead economic development organization,]</sub>

**TARGET --**

> also a resident of Lancaster City, 100 block of North Pine Street. I've made my support and complemented the city's efforts on this CBA publicly several times in addition to the letter

<sub>[context after, speaker UNKNOWN: that we submitted. So I do want to take a couple minutes to very quickly address an element of our past our present and our future as it relates to this project ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 80

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  13330.56s-13374.43s  |  98 words

<sub>[context before, speaker SPEAKER_18: already so any questions on the concept plan just to briefly cover some of the planning justifications that we believe exists for the request so again the prope ...]</sub>

**TARGET --**

> to the map and text um i think that you're making sense to me uh i do have concerns about allowing more buy right self-storage facilities though in the community um and this is just a personal view i view self-storage facilities as a cancer on long-term property values um but i can recognize the constraints you're experiencing with this site um have you considered instead of rezoning and permitting more buy right self-storage maybe special exception use for the zone you're currently in so that at least like there's more conversation because i think this makes sense

<sub>[context after, speaker SPEAKER_18: yeah this we basically arrived at this resolution after I want to say over a year of conversations with city staff in terms of yeah Eric saying years of what we ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 81

*City Council Meeting - March 25, 2025*  |  speaker `SPEAKER_20`  |  6414.1s-6418.84s  |  16 words

<sub>[context before, speaker SPEAKER_11: that right now. If I may, Vice President, I'd like to answer that question.]</sub>

**TARGET --**

> Councilor Diaz, just to wrap up a public comment, can you hold your comments until council

<sub>[context after, speaker SPEAKER_10: comments later? Thank you. Next speaker please. Hi, Sylveta Rosa, Lancaster Township. I just had a question I guess for the mayor and the other councillors if t ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 82

*City Council Meeting - February 11, 2025*  |  speaker `SPEAKER_04`  |  1318.33s-1359.06s  |  124 words

<sub>[context before, speaker SPEAKER_09: have a motion and a second councillor Arroyo Thank You council president this]</sub>

**TARGET --**

> is a resolution that is brought before council on an annual basis it is done because the city tracks water and sewers sewer usage as city properties mostly to detect leaks or unusual usage we don't bill ourselves for this usage the charges are exonerated annually to clear them from the financial accounts two properties on the list are not city owned the library and the fire line at the Lancaster Airport the water and the sewer service to the library is considered an in-kind contribution from the city and the service to the airport is done in exchange for the airport providing the city use of its large capacity snow blowers in case of a storm thank you very much council royal are

<sub>[context after, speaker SPEAKER_09: there any additional council comments on the resolution from the public hearing]</sub>

`public_comment:` ____   `note:` ____

---

## Item 83

*City Council Committee Meeting - March 3, 2025*  |  speaker `SPEAKER_07`  |  3418.9s-3936.94s  |  1245 words

<sub>[context before, speaker SPEAKER_03: good evening health members i'm pleased to be here today to share in updating you all as director campbell mentioned on lancaster's urban forestry program this  ...]</sub>

**TARGET --**

> you for the introduction so as a quick reintroduction to the trees for people plan this is the city's plan for improving our urban forests and also making sure that everyone in the city no matter their location or status has access to the benefits of trees and that natural environment it's a really well done plan and it says a lot about the city's passion for its residents and the environment that they put together such a wonderful plan most cities and municipalities while maybe they have ordinances or rules or regulations that help try to foster more canopy this plan truly is very encompassing and And definitely the envy of many other municipalities. We have been working very hard to get external funds to help support the mission of the Trees for People Plan. I have a couple of examples I want to go over real quick. We'll start with our USDA U.S. Forest Service. This was a very large grant, $1 million, which would have at least planted 500 trees by 2028. that does even sort of like while I do love planting trees as an urban forester I really like planting trees we we're gonna plant a bunch of trees but this also would have given us support for you know pruning maintenance these all sorts of other additional things that aren't just planting trees because obviously trees have to go somewhere improvements of those tree wells and such finding new tree wells and whatnot sadly this funding has currently been suspended though we are ever so hopeful that it will come back online so that we can get access to it however despite that we are moving forward and onward as well now for this summer we are very excited because we have at the urban forest reset project these are ARPA funds through our clean water partners and going to be planting 376 street trees throughout the city. This is a very holistic grant in that not only are we removing stumps or filling in empty well sites with new trees but we're also improving sidewalk and curb that have been damaged previously by the tr ...

<sub>[context after, speaker SPEAKER_09: i spoke right when i see this presentation it's it's a it's it's wonderful in so many ways you note I feel like I see street treats as something that if the cit ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 84

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_12`  |  6880.12s-6951.0s  |  174 words

<sub>[context before, speaker SPEAKER_14: Street I just want to say I think that this person should be on both of these boards so I hope in choosing any of these positions you continue that practice bec ...]</sub>

**TARGET --**

> that role that's all i had thank you thank you um i did like the idea that council had a say in selecting who sits on the board and we're taking that away again we're taking from the residents that uh the elected officials that the residents voted in to make these decisions who's sitting on these boards we do do too much uh consultant in the city with these third parties uh way too much i would like to see us looking at if council really wants to make a change talk about the process because people come and they sit through these historic commission meetings and it delays projects when we're talking about affordable housing and it's delayed and we're not talking about any other process to speed that up we're talking about who's going to sit on the board and let's change what's required of them and i think if council's really going to do something let's really speak about the process thank you thank you i'll remind everyone that this

<sub>[context after, speaker SPEAKER_30: is a first read um of this uh of this bill and it will appear i believe mr harris if i'm correct on our next meeting on the 27th is that right that's correct th ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 85

*City Council Committee Meeting - November 3, 2025*  |  speaker `SPEAKER_00`  |  8058.5s-8068.34s  |  29 words

<sub>[context before, speaker UNKNOWN: The stormwater part would not.]</sub>

**TARGET --**

> We would still be able to go forward with some of the vision 0 implementation but we would then have a sealed new installation and we would not reopen

<sub>[context after, speaker UNKNOWN: that for stormwater management at a future date. DIRECTOR DEWOLF Okay. I was just going to add that I would recommend]</sub>

`public_comment:` ____   `note:` ____

---

## Item 86

*City Council Committee Meeting - June 2, 2025*  |  speaker `SPEAKER_06`  |  5519.88s-5545.56s  |  67 words

<sub>[context before, speaker SPEAKER_03: much for giving us that introduction. Thank you, Counselor. I look forward to diving in. I look forward to seeing you again in June thank you all right so we'll ...]</sub>

**TARGET --**

> uh yes um thank you council president um this is an annual resolution to recognize world refugee day of an immigrant heritage month which is june of 2025 and world refugee day is on june 20th and this resolution is just going to honor and recognize the contributions made by both our immigrant community as well as celebrating world refugee day here in lexington and that concludes

<sub>[context after, speaker SPEAKER_03: my report great thank you so much for doing that um and counselor med uh do you have a motion on]</sub>

`public_comment:` ____   `note:` ____

---

## Item 87

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_05`  |  9532.95s-9546.06s  |  35 words

<sub>[context before, speaker SPEAKER_08: compensate the real estate agent is that or broker yes we would pay a real estate broker for their]</sub>

**TARGET --**

> work for their services currently yeah we do the same no we do currently we're precluded from using a real estate broker exactly thank you very much that's what i needed to know okay councilman

<sub>[context after, speaker SPEAKER_02: craig maybe this would help us as well typically typically uh realtors get paid once the sale of the property is complete they're not paid prior to okay so i wo ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 88

*City Council Meeting - February 11, 2025*  |  speaker `SPEAKER_08`  |  1740.54s-1773.53s  |  46 words

<sub>[context before, speaker SPEAKER_06: The $25.6 million that I was referencing just now was the amount of affordable housing investment we've made since 2018 to 2024 across many different funding st ...]</sub>

**TARGET --**

> And that is government funding, correct? Yes. OK. The other question would be, you had mentioned increased funding. The $305,000 is being allocated, is that correct? Reallocated. Reallocated. So you're going from 2020 to 2024 to show rejected funds? Can you explain that a little better?

<sub>[context after, speaker SPEAKER_09: Ms. Gomez, just to make sure you keep your time, is there anything further that you'd like Ms. Geyser to explain?]</sub>

`public_comment:` ____   `note:` ____

---

## Item 89

*City Council Committee Meeting - November 3, 2025*  |  speaker `SPEAKER_00`  |  4923.86s-4932.12s  |  13 words

<sub>[context before, speaker UNKNOWN: a motion to move this application resolution number 74 to full council on the 11th second all those in favor aye thank you so much yeah thank you all we are now ...]</sub>

**TARGET --**

> resolution number 78 authorizing the sale of 843 Fremont Street by a realtor

<sub>[context after, speaker UNKNOWN: director Delphs good to see you good to see you too council craig you have a lot of items on your committee uh i do i usually do i'm quite used]</sub>

`public_comment:` ____   `note:` ____

---

## Item 90

*City Council Committee Meeting - July 1, 2025*  |  speaker `SPEAKER_02`  |  3689.28s-3699.9s  |  14 words

<sub>[context before, speaker SPEAKER_03: come appreciate confirming my math if they don't live and work in this if they live and work in the city they would get right but if they live outside of the]</sub>

**TARGET --**

> city that could be as little as half 46 percent thank you any additional

<sub>[context after, speaker SPEAKER_08: questions or comments from council great well we have a lot to process and to think about but appreciate the report director Campbell thank you there's no actio ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 91

*City Council Committee Meeting - May 5, 2025*  |  speaker `SPEAKER_02`  |  2628.65s-2638.49s  |  27 words

<sub>[context before, speaker SPEAKER_13: but is there currently more than one building inspector yes and he is given full authority to meet these criteria he's asking for permission to make these decis ...]</sub>

**TARGET --**

> the definition and allowing for the appointment directly by the director of community planning to the board's commission authorities not to make anyone else a building inspector

<sub>[context after, speaker SPEAKER_13: i'm not saying that it's not to make anyone else it's giving him the authority to do somebody else's job no that's not correct so he's changing the definition s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 92

*City Council Committee Meeting - May 5, 2025*  |  speaker `SPEAKER_13`  |  2540.48s-2574.09s  |  67 words

<sub>[context before, speaker SPEAKER_09: are you a member of the historic society or the historic committee no i'm not and there are specific eligibility criteria for serving on the historical commissi ...]</sub>

**TARGET --**

> serve on either one of those and you're asking for a building inspector position that will be a part of another debt on top of taxpayer dollar so my question is the president of the historic society or the current building inspector are you saying that he's incapable of performing these duties or meeting these expectations and that's why you're opening up another area to oversee his

<sub>[context after, speaker SPEAKER_02: current work is that what you're implying miss Gomez can I endeavor to answer that question so this bill does not create any new positions in the city of Leices ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 93

*City Council Meeting - February 11, 2025*  |  speaker `SPEAKER_00`  |  889.01s-912.51s  |  54 words

<sub>[context before, speaker SPEAKER_09: Hirsch all right the person Baker I move into the second item on our legislative agenda this evening these are nominations for appointments councillor]</sub>

**TARGET --**

> clicks thank you madam president that this nomination was this was with you to February 3rd by the personal committee and full consoles now I'll make a motion to reappoint the Shelby Norman to the city revitalization and improvement zone authority for a term from December 31st of 2024 to December 31st of 2029

<sub>[context after, speaker SPEAKER_09: second we have a motion and a second on the appointment any additional council comments from the appointment of miss Nauman from the public hearing none mr.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 94

*City Council Meeting - June 10, 2025*  |  speaker `SPEAKER_07`  |  4209.9s-4233.4s  |  28 words

<sub>[context before, speaker SPEAKER_04: submitted thank you thank you any additional comments from the public]</sub>

**TARGET --**

> hearing none mr. Harris mr. Mudd aye mr. Arroyo abstain mr. Glees aye miss Craig aye miss Diaz mr. Hirsch aye president Baker aye thank you we will

<sub>[context after, speaker SPEAKER_04: now move into our second public comment period and this is open for issues that were not previously on the agenda this evening comments are limited to three min ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 95

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_27`  |  9926.15s-9951.23s  |  13 words

<sub>[context before, speaker SPEAKER_24: curious i think that thaddeus's architecturals have traditionally done that on each of theirs yeah the original one i believe the next street up it's in similar ...]</sub>

**TARGET --**

> neighborhood kids bicycles we know garages fill up with other stuff so you

<sub>[context after, speaker SPEAKER_24: said they do have basements right you have basements yes yes um yep and then uh forgive]</sub>

`public_comment:` ____   `note:` ____

---

## Item 96

*City Council Committee Meeting - July 15, 2025*  |  speaker `SPEAKER_07`  |  1373.67s-1436.78s  |  147 words

<sub>[context before, speaker SPEAKER_03: allocations? Well you always have to do annually annual allocations that being said the admin code just set up a whole series of financial policies, financial g ...]</sub>

**TARGET --**

> And I would just add that in contrast to the Home Rule Charter, which cannot be changed changed the admin code can also be changed on a regular basis and and a budget is my understanding has always been that a budget is an annual allocation and that you cannot make commitments for future budget years but you can have policy guidance to direct the allocation or the capital or capital reserves or whatever policy statement there is but annually you would still need to have that budget allocation and because it's an annual allocation just the same that there's obviously policy that is embedded into a budget at the same time you can change the admin code so even if you're trying to prioritize it through the admin code the place where it is going to effectuate the most changes actually in the budget yeah and

<sub>[context after, speaker SPEAKER_05: that's that was that was really the basis of my question was kind of from like the policy side and like can we set policies that would affect future]</sub>

`public_comment:` ____   `note:` ____

---

## Item 97

*City Council Committee Meeting - June 2, 2025*  |  speaker `SPEAKER_01`  |  1763.71s-1793.37s  |  62 words

<sub>[context before, speaker SPEAKER_10: really be comfortable with uh your ability to understand the issues and to really analyze the issue and then like you said make sure that your your personal opi ...]</sub>

**TARGET --**

> proactively guide city officials on how to make good decisions that reflect the values of justice diversity transparency and community benefit considering both the intended and unintended impacts of the decisions we make and the desires that our residents have for their communities so that's what really brings me uh here to this table thank you so much i'll do it now

<sub>[context after, speaker SPEAKER_04: so how do you see yourself holding accountability to checks and balance needed for the city and the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 98

*City Council Meeting - June 10, 2025*  |  speaker `SPEAKER_18`  |  788.1s-799.87s  |  2 words

<sub>[context before, speaker SPEAKER_05: Thank you, Council President. I believe Zaira from the City Language Access Program is also going to be speaking.]</sub>

**TARGET --**

> Thank you.

<sub>[context after, speaker SPEAKER_04: Thank you.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 99

*City Council Meeting - August 12, 2025*  |  speaker `SPEAKER_20`  |  4028.91s-4205.96s  |  610 words

<sub>[context before, speaker SPEAKER_11: and then may I also have you start with your block of residence? Thank you, oh, I'm sorry. So I'm in the 100 block of North Main.]</sub>

**TARGET --**

> Thank you. So I have a couple points, a couple questions, and a charge to the council. So first, I wanna say that for those of us that were here I think it was maybe two city council meetings ago we heard the budget and all of the information about where our money is being spent you may have remembered that the storm the wastewater treatment plant had to purchase a quote-unquote sliver of land from PPL and that required a land development plan so we who own the wastewater treatment plant we're doing a land development plan to ourselves the city and yet the AI data center now they don't need one we don't have to worry about them doing one we'll just trust them. That is ludicrous. That is preposterous. Two, I am very concerned with the fact that the governor and the mayor are both so gung-ho about this. And frankly, the mayor, I understand that you have said there's little we can do. There are restrictions in place. There are things that we can't undo. What you could do is speak out. You could say, we are not welcome here. We can't stop you, but you're not welcome here. You could say, Lancaster is closed for business for AI data centers in the future. It's not that hard. So your sort of cavalier and frankly dismissive attitude tonight makes me think that you are fully full-throated in behavior in in favor of these. So here are some questions. Who is going to be responsible for checking to make sure that these data centers do not go one inch outside of the current footprint which would then of course trigger all sorts of oversight? Two, who is going to be responsible for making sure that these diesel generators are only operated as testing during the day as the requirement says three who's gonna make sure that those generators do not operate for more than 100 hours per month as the agreement says for who's gonna make sure that they never switch to water cooling down the line after we have let them come in and we say oh well they're already here we don't really have any ...

<sub>[context after, speaker SPEAKER_11: Thank you, Mr. Levine. there was one additional speaker who wasn't present when their name was called that was gerald weiner so i'd like to give them the opport ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 100

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_06`  |  12649.92s-12707.86s  |  201 words

<sub>[context before, speaker SPEAKER_14: this since 2017 name me a class 3 city that has any teeth show me the point is]</sub>

**TARGET --**

> that I answered the exam question but what I'm asking in response is for written stuff the public can read on their own time so we can get educated as well as y'all who are gonna be here next year so actually what I would recommend recommend instead of January, and I'm asking this of you specifically, counselor or med, I'd love it if that in February of next year, after you've returned to council, you request this conversation be brought to the public safety subcommittee with some of this documentation. Not because, yeah, this thing was so flawed. Clearly, it was flawed from the beginning when I put it together, because I was of the perspective based off someone up here on the dais that advisory would be fine. But then it got met with a bunch of hurdles. What we as the public need to help you move forward is information so i guess i'm asking you are you willing to get some of this information prepared over the next five months for us not all at once but just are you willing to work towards this and revisit this issue again in february once all the budget stuff

<sub>[context after, speaker SPEAKER_26: has died down and everything new is in place i mean i'll answer your question mr dastra and uh as been stated by other members of council and other members of t ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 101

*City Council Budget Hearing - October 21, 2025*  |  speaker `UNKNOWN`  |  8302.94s-8342.04s  |  114 words

<sub>[context before, speaker SPEAKER_00: young to retire I have two two questions kind of in the weeds maybe a little bit but um so you're probably thankful that this is your last budget that you need  ...]</sub>

**TARGET --**

> exactly does that mean so it came out of a different line item before so the new line item was added so um every night after hours there's a duty captain who takes calls um and basically you know the the shift oic the lieutenant working or sergeant will handle this you know any issues that come up if there is you know a homicide or if they have a question or there's a shooting or there's something that may generate news uh they could go down a range of different reasons why they would call one of the the duty captain and it could be to get advice to advise them of something

<sub>[context after, speaker SPEAKER_00: and that's the compensation for that got it and then i also noticed an increase for community]</sub>

`public_comment:` ____   `note:` ____

---

## Item 102

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_28`  |  5917.98s-5930.66s  |  33 words

<sub>[context before, speaker SPEAKER_20: just be talking about setbacks and storm water wouldn't actually be yeah so by that at that point]</sub>

**TARGET --**

> the horse would already left the barn right and that's it's typical typically zoning has to be approved before it comes before you for subdivision land development so i want to jump in

<sub>[context after, speaker SPEAKER_09: here a little bit um i'm glad we're talking about having a public hearing the conversation about getting that on an agenda should continue because we do have an ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 103

*City Council Committee Meeting - May 5, 2025*  |  speaker `SPEAKER_11`  |  2027.95s-2044.48s  |  33 words

<sub>[context before, speaker SPEAKER_06: any questions from the public jose rivera honey block of corn my question is are we getting a new]</sub>

**TARGET --**

> water station you know because that whole thing is like only 1800s for that particular um well yes all the tainted water and everything what they'll do is they'll expand the capacity for

<sub>[context after, speaker SPEAKER_06: for that development but you're not fixing the main project the whole name]</sub>

`public_comment:` ____   `note:` ____

---

## Item 104

*City Council Committee Meeting - November 3, 2025*  |  speaker `UNKNOWN`  |  7956.0s-8044.98s  |  212 words

<sub>[context before, speaker SPEAKER_00: i will open it up to questions from the public works committee or full council]</sub>

**TARGET --**

> and i'll also offer are there any comments uh or questions from the public um darlene bird ann street i know we borrowed a lot of money for stormwater and for sewer we just had another pen vest grant how much of the city is not covered in the money that we're borrowing that we're looking to take a million dollars to just do raw street are there other areas in the city that will not be included in all the money that we borrow to do water and stormwater management so i do think that's a good question but this the advantage of this is that it's a grant so if we do not have access to this it really is the case that we may not be able to take advantage of this opportunity and provide stormwater management at this particular location we just do not have other funds does not include the whole city there are areas that are excluded from the plan that we presented I was here last year that we presented when we got bonds for all this that we went into debt for it didn't include doing stormwater management for the city just certain areas. If I could venture to answer your question I think

<sub>[context after, speaker SPEAKER_00: what I'm hearing Director Campbell saying is that for one this particular project would not go forward without the grant like without the grant it's not going t ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 105

*City Council Meeting - November 11, 2025*  |  speaker `UNKNOWN`  |  2883.49s-2929.14s  |  102 words

<sub>[context before, speaker SPEAKER_00: orange um i just want a second uh darlene bird's attempt to get an answer for that thank you]</sub>

**TARGET --**

> thank you i don't think we have that to repeat i don't think we have the information from the proposed tenant of that particular space that would be up to them Any additional comments in the public on the bill on bill 14? Good evening. Good evening My name is Carlo Gonzalez from 300 block or so any street and also member of a southern consent enable The same we come back again to try to find some answer about what we request in the last couple week meeting What going on with Ali? 59 and what going on with mr. Tom

<sub>[context after, speaker SPEAKER_00: Snyder, what is the real goal he pretend to do in our neighborhood, because according to what we see, he pretend to bring his business of heavy truck, whole tru ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 106

*City Council Meeting - March 25, 2025*  |  speaker `SPEAKER_24`  |  7002.56s-7006.06s  |  2 words

<sub>[context before, speaker SPEAKER_25: yeah sucks. Next speaker please. Hello my name is Betty Jones South End Concerned Neighbors. My address is 222 South End. I'm calling I mean I'm here to talk ab ...]</sub>

**TARGET --**

> thank you

<sub>[context after, speaker SPEAKER_13: mrs jones i'm meeting with uh director campbell tomorrow and i i know that miss bird had also followed up and i thought that um we had gotten some more informat ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 107

*City Council Committee Meeting - November 3, 2025*  |  speaker `SPEAKER_00`  |  4806.67s-4826.32s  |  41 words

<sub>[context before, speaker UNKNOWN: questions we are super eager to get to work on this one we just need a bit more]</sub>

**TARGET --**

> money okay questions from the committee questions from council as a whole Thank You councillor Craig you made mention of the funding delay is that directly related to the state budget impasse is that why LSA has been delayed in general

<sub>[context after, speaker UNKNOWN: it's a long process but is it is that the reason why we're still waiting on 2024 do you have I see Jenna sort of nodding in the background I mean I can't]</sub>

`public_comment:` ____   `note:` ____

---

## Item 108

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_28`  |  5348.77s-5379.72s  |  96 words

<sub>[context before, speaker SPEAKER_16: i have two questions and maybe for um lauren or betsy so if we if we do want to hold a public hearing what what actually needs to happen for that so that's ques ...]</sub>

**TARGET --**

> look like so sure so i'll start with that um is my mic working okay um so i would say for the um request from city council i would say it's rather vague in the ordinance both in the municipality's planning code and in our zoning ordinance it just says that it's to come from the city council i think in discussions with um our solicitor and staff that it would be like a city council um decision as a whole body to move it forward okay and can i can i just follow up on

<sub>[context after, speaker SPEAKER_16: that can you i guess i'm a little curious about the precedent for that because i you know i remember i was on the planning commission when we amended the zoning ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 109

*City Council Meeting - March 25, 2025*  |  speaker `SPEAKER_08`  |  4542.29s-4662.73s  |  350 words

<sub>[context before, speaker SPEAKER_03: I appreciate that, Councilor Emmett. Now, so then the question is, where's the real list of what you'll be getting rid of? And how do you really prove that that ...]</sub>

**TARGET --**

> tabled again my comment on that I second that this is an extremely tone-deaf thing to put forward to us at this moment in time I think it's disgusting that we would even could talk about it I hope that each and every single one of you votes nay because this is the kind of thing that you know we talked about a public review board and this is the kind of thing that a public review board should be looking at not the police force not you guys us because it's ridiculous that you know we keep talking about these issues with police violence and police violence all over the country and yet you are here talking about what 21 22 that's only three years ago that's not long enough they've been commit they've been doing police violence for the past few for like decades I don't want those records gone I want each and every single one of them held accountable for what they've done this is like each and every single one of you needs to vote no just flat out i don't even want a table i want it gone i want a public review commission they're the ones that should be making these decisions not the police not us i don't trust the police force they've shown over the over their last statements we cannot trust them why do you think i would trust them to throw something in the shredder i can't i can't even trust them with the evidence that they gather from somebody's home let alone the evidence that's sitting right in their own halls so I'm sorry I'm just flustered right now because it's baffling I I came here because I saw this on the agenda I saw it and this is why I'm here because this is ridiculous and you guys need to vote no or I hope that each and every single one of you gets a challenge for your seat I don't think that you deserve a seat on that council if you vote for this so again

<sub>[context after, speaker SPEAKER_17: this council creates Commission of black and brown affairs related to police brutality this was related to police brutality you're telling me that in 2020 you h ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 110

*City Council Meeting - July 8, 2025*  |  speaker `SPEAKER_10`  |  2646.38s-2719.74s  |  164 words

<sub>[context before, speaker SPEAKER_06: grievous and i i am on the 400 block of west end avenue i am here to formally express my concerns regarding the handling of code enforcement inspections on my p ...]</sub>

**TARGET --**

> Good evening. My name is Ellen Sloan. I live in the first block of North Lyme Street. I'm reaching out because our city must take urgent steps to respond to the rise in masked law enforcement, ICE overreach, and the targeting of immigrants and political dissenters, including students and lawful residents. As local officials, you have real power to protect our communities. i'm urging you to pass a city ordinance requiring visible identification for all law enforcement operating within city limits including federal agents prohibit local police from cooperating with or facilitating ice operations especially those that occur without warrants or clear justification to work with the school district and other educational institutions and our hospital to establish and or double down on local sanctuary policies and rapid response systems when federal agents attempt enforcement actions the rise of secret policing and disappearances is not just a federal issue it's a local emergency our city should be a place of safety not surveillance and

<sub>[context after, speaker SPEAKER_08: fear thank you miss lynn thank you thank you are there any additional public comments for this]</sub>

`public_comment:` ____   `note:` ____

---

## Item 111

*City Council Committee Meeting - August 11, 2025*  |  speaker `SPEAKER_09`  |  1112.12s-1155.86s  |  101 words

<sub>[context before, speaker SPEAKER_13: particular that you would like to achieve during your term on the board yeah there are a lot of]</sub>

**TARGET --**

> codes that Lancaster City amends every so often and I have found that it's a little difficult to get the word out to the other plumbers I think it would be good at least with my knowledge and my connections that I can get that word out so all the plumbers can come together and you know successfully you know plumb this place in you know so yeah but with my extensive knowledge in the plumbing code only with the IPC and the local codes this is yeah this is really exciting for me thank you are there any questions or

<sub>[context after, speaker SPEAKER_13: comments for members of the committee please consider her just want to say]</sub>

`public_comment:` ____   `note:` ____

---

## Item 112

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  14266.41s-14299.45s  |  102 words

<sub>[context before, speaker SPEAKER_22: happening that we pent up demand is pushing all the self-storage into places it doesn't want to be can't really be controlled from a security standpoint from ju ...]</sub>

**TARGET --**

> in the location i mean your traffic constraints are valid f m's right there though so the students probably could utilize that property a lot for self-storage but i think i don't think anyone up here is concerned about this specific proposal it's just a concern about what other proposals might come from it uh in the interim of like like i said earlier like we need to do the overall comprehensive plan update which isn't your fault um so i'd like to see you move forward but i i'd also think there is a need for pause that's just my opinion

<sub>[context after, speaker SPEAKER_04: right if we if we were to go down to like three to five acres um for example then that would be 16 parcels three of which are vacant land so that would reduce t ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 113

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_24`  |  10896.68s-10925.2s  |  69 words

<sub>[context before, speaker SPEAKER_16: That's still running a red light, I guess. So that's what would be covered.]</sub>

**TARGET --**

> So the question is, could the, what these cameras ticket be changed in the future? only with legislative changes for at the state level okay now the this in chicago they changed the timing of yellow lights they shortened the yellow lights to increase um the by a tenth of a second is is there any chance that that would happen here no i would say there's something in

<sub>[context after, speaker SPEAKER_20: the ordinance i was just reading that says that we can't deviate from the standard set by the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 114

*City Council Committee Meeting - July 15, 2025*  |  speaker `SPEAKER_06`  |  1012.21s-1024.13s  |  34 words

<sub>[context before, speaker SPEAKER_03: anything else and i'll i'll just go around council councilman correct i i don't have anything further]</sub>

**TARGET --**

> uh councilman arroyo i actually don't have any questions or comments i thought um yeah i thought the changes that were suggested during the last reading were very valid and yeah feel good about

<sub>[context after, speaker SPEAKER_00: it councilman hirsch i just had one question um section three which is on page 25 of the admin code that's before us it talks about the sale of personal propert ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 115

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_08`  |  9774.27s-9816.19s  |  113 words

<sub>[context before, speaker SPEAKER_03: i guess i would just hope that we would still have the ability of the intention of what that property]</sub>

**TARGET --**

> becomes that's also through a whole zoning process and so um and that information that we've collected related to zoning uh for that particular parcel would be part of the sale and typically sales of properties in the city of langley lancaster are contingent have contingencies related to them getting zoning approval for anything that they would use the product for which is the opportunity for the public to weigh in if they don't like the concept that's being there and so we would likely sign a sales agreement that would be contingent upon them getting the approvals that they need and if they don't get them then the property wouldn't be sold

<sub>[context after, speaker SPEAKER_03: that is a very standard practice thank you and that answers some of my questions but i look]</sub>

`public_comment:` ____   `note:` ____

---

## Item 116

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  6223.6s-6309.56s  |  249 words

<sub>[context before, speaker UNKNOWN: and understand what it all entails we need more time i think that you should postpone the vote on this for at least one week and i think that you should put the ...]</sub>

**TARGET --**

> so that people can have input so that people can ask questions and have concerns and suggest things that may have that you all might not have considered all of that aside i have two questions the first is does this hold weight in the part of the greenfield center that is outside of our outside of the city's jurisdiction so does east lampeter uh does the east lampeter part have uh do they also benefit from this and then the second question is who is actually involved in this is it the owners the developers or the tenants or all of the above because i see the owners listed on the agreement and you all keep talking about the developers so which one is it if I could endeavor to answer those questions with the remainder of your time if that would be okay yes Eastland Peter benefit so they were not a party to the agreement but they benefit because they're so close so the environmental and quality of life benefits anyone on the Eastland Peter side of that I would say second part of your question I apologize say that last part again who is actually involved in the agreement is it the developers owners of the tenants the developers and the owners are one in the same the parties to the agreement are the LLC's that have been developed for the management but it's the same parties so the parties of the agreement are the

<sub>[context after, speaker UNKNOWN: city and the owners of the property which is to say the developer so the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 117

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_25`  |  10433.3s-10464.69s  |  56 words

<sub>[context before, speaker SPEAKER_30: I appreciate but we've reached past three minutes thank you doesn't sound like it are there any additional comments for this period]</sub>

**TARGET --**

> Taylor Raymond 500 block of st. Joseph Street I'm glad that you passed the resolution in favor of House Bill 1150 to raise the minimum wage putting pressure on the state to pass that if I understood correctly that would also give power to more local governments to set minimum wage in lower are in smaller

<sub>[context after, speaker SPEAKER_30: districts is that correct I believe that's what representative Rivera had mentioned that was in the current version of the House bill the the ability for munici ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 118

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_08`  |  4187.1s-4374.56s  |  507 words

<sub>[context before, speaker SPEAKER_30: commenters for this period no they're not thank you we will now move to our next item on the agenda which is reports requested by council tonight we have a pres ...]</sub>

**TARGET --**

> good evening mayor sirachi council president and members of council i'm here this evening on behalf of joshua f who's not able to join us but has worked so hard the last six months with the students that are here and i know he's watching us so if we can just give him a round of applause he's so sad that he's not here we miss you josh and um it's an honor he did actually he has a write-up so i just want to share some of his words so good evening mayor sirachi members of council and neighbors of lancaster my name is joshua and i serve as the engagement specialist in the department of neighborhood engagement i have the privilege of managing engagement programs and working with community leaders over the past six months i've had the honor of guiding an incredible group of students from jp mccaskey school and through the neighborhood leadership academy these young people have impressed me so much from day one their level of commitment curiosity and care for their community has been so inspiring to me together we explored how local government works how neighbors can collaborate to create positive change and most importantly how essential youth voices are in building a stronger and more inclusive lancaster the student cohort is part of a larger initiative that began in 2019 and since then we've led a total of 10 neighborhood leadership academy groups with over 160 residents participating across the city and some of them are also represented here this evening the program continues to serve as a powerful tool for education empowerment and community connections a recent highlight was the students involvement in the traffic garden project during open streets this past saturday they partner with the department of public works to design a bike safety course use chalk paint to create the layout and taught younger children about stop signs yielding and pedestrian safety all through a hands-on biking simulation that they created it was a proud moment that showed what's possible whe ...

<sub>[context after, speaker SPEAKER_34: good evening my name is jose tesfai and i live on the 300 block on voltaire boulevard good evening mayor sirachi members of city council and distinguished guest ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 119

*City Council Committee Meeting - February 3, 2025*  |  speaker `SPEAKER_02`  |  4380.27s-4472.74s  |  205 words

<sub>[context before, speaker SPEAKER_06: Weiss it is February the shortest month of the year and here we are at Black History Month again so I'm going to first ask is there anybody here that would like ...]</sub>

**TARGET --**

> that concludes that thank you councillor craig and i appreciate you reading the resolution any questions or comments from full council from the public with that i'll motion to move resolution number 9 2025 to full council all those in favor aye next item on the agenda is the administration resolution number 11 2025 which is authorizing a flag raising at City Hall to mark Pride Month this resolution was brought to us through an application by the Lancaster Pride Association which has submitted its application to the city of Lancaster in a timely manner that is requesting that the pride flag be flown at City Hall on June 2nd 2025 with a back-up date of June 3rd 2025 in case of inclement weather any questions or comments from full council any from the public with that all motion to move administration resolution number 11 2025 to full council second all those in favor all right that concludes our committee of the whole will now move to the clerk's report mr. Harris I believe you submitted that to us in writing I did yes great I'll ask counsel to review the written report with that I will conclude a city council committee motion to adjourn

<sub>[context after, speaker SPEAKER_12: second second all those in favor aye meeting adjourned thank you]</sub>

`public_comment:` ____   `note:` ____

---

## Item 120

*City Council Meeting - April 8, 2025*  |  speaker `SPEAKER_17`  |  4716.54s-4796.43s  |  213 words

<sub>[context before, speaker SPEAKER_05: basically accelerated the timeline on this process mm-hmm and out of the interior lines as well I didn't know I don't know if you want to speak to that]</sub>

**TARGET --**

> Mr. Rauch just to say the city has been replacing lead laterals off the water lines for decades which is why we have so few the the new law that has been passed both accelerates the remaining replacement of those lead lines those laterals of which there are less than 1% out of the 50,000 lines that are across our water distribution service area what is new is that this utilities are now responsible for the line that is coming from the curb into the house that was only ever contemplated as being private property and under the Biden administration that law was changed and so the city has been doing work that it has been required to do to replace all of our laterals what is new is the replacement of what would have been previously understood as private property that is now our job that is now a burden that repairs will have to carry because there is not enough federal grant money to meet the demand across the country and this is a point of advocacy through the Water Council and the US Conference of Mayors and other groups that I'm affiliated with because they do understand the impact of our repairs but it has it but it was a

<sub>[context after, speaker SPEAKER_18: problem it's always been a problem and it's I'm sorry once it then when when is the deadline hearse no the deadline that you have we're already at the 10th year ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 121

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_07`  |  5302.19s-5311.55s  |  29 words

<sub>[context before, speaker SPEAKER_02: by which before we would vote on this thank you good evening I can provide some clarification there were two items on the harp committee meeting the one that is ...]</sub>

**TARGET --**

> resolved and you're saying that's not any of the items that are on the agenda tonight the one that was tabled okay I just wanted to clarify thank you

<sub>[context after, speaker SPEAKER_30: councillor Hirsch any additional council comments from the public]</sub>

`public_comment:` ____   `note:` ____

---

## Item 122

*City Council Special Meeting - November 20, 2025*  |  speaker `UNKNOWN`  |  5691.66s-5700.42s  |  31 words

<sub>[context before, speaker SPEAKER_00: Was addressed in the first part of our presentation about the limits 20,000 gallons, which is a fourth of the use Previous at this at this site. We don't need r ...]</sub>

**TARGET --**

> thank you and I would also just add that they're in addition to them not being in the looted district there are no other tax incentives that the city is offering

<sub>[context after, speaker SPEAKER_00: for either of these properties thank you I would like to follow up with a question so they can still apply through the county is that correct or not the way the ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 123

*City Council Committee Meeting - September 2, 2025*  |  speaker `SPEAKER_15`  |  4236.36s-4355.28s  |  246 words

<sub>[context before, speaker SPEAKER_14: brought forward by councillor Hirsch Thank You vice president Arroyo this resolution I'm bringing forward to you all I sent you so awesome information yesterday ...]</sub>

**TARGET --**

> are none i will open up to comments from the public elizabeth hoffman 200 block of east ross and thank you very much counselor hirsch for taking this on i'm with a group called third act pennsylvania it's people in their third act of life and we're working on climate change and democracy and this bill is a big focus of our work we're working with a lot of other organizations in like a group called our solar PA and Pennsylvania has been trying to pass this for ten years now this is the eleventh year it's a great way for people who can't afford to put solar on the roof or if their house is too shady or the renters whatever they subscribe to a solar project so they're not actually owning it leasing it or anything they're just subscribing it and I did have this in Maryland and it's you know you don't notice it on your bill there's consolidated billing so you just select that you want to subscribe to a project and you get a credit and you're putting solar electrons on the grid so Pennsylvania is 49th it ranks 49th in the growth of renewable energy so we're really falling behind we only we get less than 1% of our energy from solar so we think this is an easy way to add solar to the grid and thank you again for considering it are there any other comments from the

<sub>[context after, speaker SPEAKER_02: public why people can't do this already I mean like what about this bill makes this it people able to do it doesn't you know like why why do we need this bill s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 124

*City Council Meeting - March 11, 2025*  |  speaker `SPEAKER_10`  |  7769.63s-8021.96s  |  601 words

<sub>[context before, speaker SPEAKER_29: that's all I have to say typically we we have a one three minutes but it's your first meeting and I'm sure being here so all right honestly I wanted a Cordell]</sub>

**TARGET --**

> booth 400 block Lucas I just said what that lady said before me I forgot her name i'm sorry uh she's right what the hell are the school resource officers doing at my school listen i respect them i talk to them i try to communicate with them i mean for when i see them they don't do anything they sit in the hallways and they watch and wait for probably students to get into a fight that's not okay and i want them to start teaching students that are uneducated about what they can about laws because it's not okay and i want my friends to be safe in my community my friends invited me to play basketball tonight at the park and i told them no because i wanted to be here because this was a little bit more important than playing basketball but also because i remember being in middle school and i was at that park and there were two of my of two other people on the other side of the court getting absolutely harassed by officers asking them questions and harassing them and i didn't say a word because i was scared i'm not scared anymore i mean miss baker you heard you said it i'm trying to make my mom proud right now and every single day that i go out and i represent her and my dad i want to make i want to make them proud man and every day that i see kids that are going through this absolute bs i can't take it anymore and i'm not just going to like stand by and let it happen and i'm going and i really do want the mayor to be here and i want the chief of police to be here because they need to hear me and all of these other people talk about what they should do because again as i've repeatedly had to say it's not okay it's not when i leave next year when i go off to college whichever one of you two is the mayor whichever one which i will be voting in because i'll be 18. but whichever one you use the mayor how are you going to protect my friends that are still at mccaskey that are still in the middle schools that are still at these programs that i summer camp council at for months t ...

<sub>[context after, speaker SPEAKER_29: along with everybody else all right that's all i got an opportunity as i mentioned before for the folks that might have been on the list for the first public co ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 125

*City Council Budget Hearing - November 18, 2025*  |  speaker `UNKNOWN`  |  4927.0s-4931.7s  |  15 words

<sub>[context before, speaker SPEAKER_00: was one of the things that we did we have an opportunity and now with our expansion we were able to expand for more vendors so we want more vendors]</sub>

**TARGET --**

> more different types of vendors that are selling not only food but can we have

<sub>[context after, speaker SPEAKER_00: cultural items also represented there that's one of the things we're also one]</sub>

`public_comment:` ____   `note:` ____

---

## Item 126

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_19`  |  5094.09s-5111.45s  |  41 words

<sub>[context before, speaker SPEAKER_30: ECONOMIC DEVELOPMENT COMMITTEE COUNCILOR EMED THANK YOU COUNCIL PRESIDENT THE ECONOMIC DEVELOPMENT COMMITTEE DID NOT THANK YOU FINANCE COMMITTEE COUNCILOR ARROY ...]</sub>

**TARGET --**

> THE FINANCE COMMITTEE DID MEET DURING THE LAST SESSION TO DISCUSS RESOLUTION ADMINISTRATION RESOLUTION NUMBER 37-2025 WHICH AUTHORIZES THE DONATION OF 339-341 BEAVER STREET TO SACA development corporation and that will be discussed later this evening on the agenda that concludes

<sub>[context after, speaker SPEAKER_30: my report council president thank you community planning committee councillor craig thank you]</sub>

`public_comment:` ____   `note:` ____

---

## Item 127

*City Council Committee Meeting - November 3, 2025*  |  speaker `UNKNOWN`  |  4001.47s-4017.23s  |  54 words

<sub>[context before, speaker SPEAKER_00: when you go into the medical, we see over 10,000 patients a year at that location. It's extremely]</sub>

**TARGET --**

> busy, but it looks like a bit of a 90s location. So we're looking for local shares to help us fund the renovation of that location. We plan to be there for several more generations. We've been there for several decades already, and we'll be requesting a million dollars in LSA money to be

<sub>[context after, speaker SPEAKER_00: able to fully renovate the first floor to kind of bring the technology and the space needs up to the 21st century happy to answer any questions spectacular are  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 128

*HARB Meeting March 4 2025*  |  speaker `SPEAKER_02`  |  238.1s-260.48s  |  75 words

<sub>[context before, speaker SPEAKER_03: any questions or comments from the board just the one comment um suzanne this is really not so much about the proposed window but about the mention of change in ...]</sub>

**TARGET --**

> to come before mr evangelista he does not because he's it's the business doesn't have a lot of walking customers he's just using his warehouse he doesn't have any signage plan to be mounted on the exterior which you would review if he just has a decal or something on the inside window or door that would not be review okay you want to mount a sign on the wall or a bracket okay it's

<sub>[context after, speaker SPEAKER_00: good enough for the future yeah we don't have any plans of that but you're saying if we do want to do something in the future that's kind of revisit that okay g ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 129

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  4208.77s-4236.62s  |  69 words

<sub>[context before, speaker SPEAKER_15: we don't need to paint things you don't need to uh a lot of these materials don't require a lot of maintenance and i think that's that's helpful for lots of gen ...]</sub>

**TARGET --**

> you had also said that you tested this theory and it so it works um as i understand it your existing units are short-term rentals so how does those two short-term rentals translate to the success of a i'm counting 79 housing for sale development complex it's completely different market how does that translate to proving that this is good yeah i think uh i think it's one of

<sub>[context after, speaker SPEAKER_15: those nuanced uh you can't quite put your finger on it but i think it's a um it was a vision and an idea that we had hey can we make this work and can we embed  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 130

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_20`  |  8449.86s-8462.55s  |  16 words

<sub>[context before, speaker SPEAKER_04: square footage of these units um good question]</sub>

**TARGET --**

> will these be rental or for sale units okay so uh not opposed to not providing

<sub>[context after, speaker SPEAKER_09: off-street parking because we do need to progress towards a less car-centric world um with the size of these so roughly 600 square feet them being single family ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 131

*Traffic Commission Meeting - November 11, 2025*  |  speaker `SPEAKER_00`  |  2948.92s-2956.88s  |  19 words

<sub>[context before, speaker UNKNOWN: And like one of the previous comments said, With it being the first two-way street,]</sub>

**TARGET --**

> it's not a spot where people really stop and look. I've also seen two or three, at least two,

<sub>[context after, speaker UNKNOWN: maybe three people turn the wrong way onto Mary off Lemons.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 132

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_15`  |  5808.2s-5885.52s  |  176 words

<sub>[context before, speaker SPEAKER_17: really appreciate from the planning staff can you help me understand why we should allow you to negotiate through certain processes and procedures when we do no ...]</sub>

**TARGET --**

> think so i think it's more of a i think it's more of an understanding of intent i'm not asking an engineer to give way or undermine a design i am asking for intent to be appreciated like it like again like the last project was the last project was in the same place i just so happened again because of foresight and thoughtfulness i did not have to put in curbs like that technically was a waiver probably i did not have to install sidewalks that was probably a waiver i did not have to do a lot of things over there because it doesn't make any sense to do that there's not a single sidewalk or curb in sunny side right now and so we're trying again to do this thing and i and i get it um you want the city ordinance is designed to produce streets that look like king street that look like chestnut street not sunny side not davis with all due respect sir i think you're running two issues

<sub>[context after, speaker SPEAKER_21: together here there's a lot of flexibility in the flexible residential development options that's why it's called that you're allowed to do many things that are ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 133

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_32`  |  4451.72s-4503.26s  |  117 words

<sub>[context before, speaker SPEAKER_34: good evening my name is jose tesfai and i live on the 300 block on voltaire boulevard good evening mayor sirachi members of city council and distinguished guest ...]</sub>

**TARGET --**

> execution my name is Jonathan Peters I live on the 700 block of Marietta and the biggest experience that we did as a part of NLA is that we planned a pop-up traffic garden during open streets on Saturday and all of the people you see here today spent somewhere between three and six hours there setting it up and also running an example to the kids on how to conform to road safety essentially what we did is we designed signs questions and the layout of the pop-up garden for kids to bring bikes and come bike around in the area and throughout the day we would walk them around explain to them what the signs

<sub>[context after, speaker SPEAKER_33: meant and teach them about road safety my name is Kai I'm from the 200th block of of north pine street um and i'm going to share some reflections on the neighbo ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 134

*City Council Committee Meeting - June 2, 2025*  |  speaker `SPEAKER_10`  |  844.32s-908.66s  |  119 words

<sub>[context before, speaker SPEAKER_07: that your personal beliefs don't necessarily conflict with your responsibility to be an impartial uh uh arbiter or mediator um how how would i really not unders ...]</sub>

**TARGET --**

> of being neutral okay that was sorry that's a little more concise yeah um during my tenure at Thaddeus Stevens, I ran and orchestrated or organized a program where we had to bring a lot of folks in to check out their ability to be biased in some of the decision-making pertaining to the college itself, its programs, its students, and things like that. I myself you know, had to make sure that my biases didn't impact any of my decisions, and I'm pretty comfortable with separating myself from the issue at hand, my biases and feelings and things of that nature to the issue at hand and deal with only the facts. Thank you. Thank you. I'll go.

<sub>[context after, speaker SPEAKER_03: I'll just help him as we go around. Mr. Colbert, thank you again for being here tonight. This is, of course, a volunteer position. Have you ever served on any o ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 135

*City Council Special Meeting - November 20, 2025*  |  speaker `SPEAKER_00`  |  6526.36s-6753.95s  |  707 words

<sub>[context before, speaker UNKNOWN: risk. It's possible that if we don't sign this agreement, they build anyway, they win the court]</sub>

**TARGET --**

> case, and they just pollute and do whatever they want. Now, they're already bound by the state and federal laws, though I really appreciate them agreeing that they will be bound by the laws. So I think it's potentially in our benefit to just say, no, we're not going to do that. Then we gum up the works. We do everything we can to slow down their construction. We do everything to make it uncomfortable for them. And then all of us here, we go protest. We protest. We block construction. We do everything it takes to slow this down. They don't want that. They want us to just say, oh, well, I guess it's the best we could get. I don't think that's a good idea. and then lastly I would love to know if any members of the city of the city government and or the mayor signed an NDA and now I know the nature of NDAs are that you're not gonna say yes I signed an NDA but whether it's here or in public I'm gonna take anything other than a resounding no as yes that you did and I think that is a huge problem there was a huge article that just came out saying they're all requiring city officials to sign NDAs and then to block FOIA requests that is a huge problem and I would feel much more trust I would have much more trust if I knew for sure that that did not happen with anyone here including the zoning director who just single-handedly approved this thank you no I was not asked to sign an NDA I'll allow any member of council who wishes to to make no I did not sign an NDA I did not sign an NDA I was asked I i did not sign an nda i did not sign an nda at all i did not sign an nda i did not sign an nda thank you good evening good evening my name is eric souder i'm from east petersburg i am the founder of regional local climate organization i'd like to thank the city for your work on this it's a very thoughtful document as has been mentioned i believe there are numerous impacts like land use water consumption and on-site emissions that could actually be significantly worse if these data c ...

<sub>[context after, speaker UNKNOWN: to install solar and satisfy the requirement.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 136

*City Council Meeting - August 12, 2025*  |  speaker `SPEAKER_07`  |  3354.46s-3361.11s  |  18 words

<sub>[context before, speaker SPEAKER_11: Thank you. Mr. Harris, our next speaker, please.]</sub>

**TARGET --**

> next is i'm sorry lindsay fitting good evening hello my name is lindsay fitting i live on the

<sub>[context after, speaker SPEAKER_16: 500 block of west james street and i'm here to talk about you guessed it the ai data centers so as a resident of lancaster city i fear for our access to water a ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 137

*City Council Meeting - April 29, 2025*  |  speaker `SPEAKER_09`  |  3688.04s-3904.0s  |  362 words

<sub>[context before, speaker SPEAKER_17: Thank you. Yes, Ms. Butler, there you are. Good evening.]</sub>

**TARGET --**

> Good evening. Thank you for giving me this opportunity to speak in front of you, and thank you for all that you do. This is my second or third time here. My apologies. I want to read something. Please do not disturb me. i don't know who you are but don't do that please continue your comments toward council janet diaz is a well-known figure in lancaster serving on the city council since 2017 as the first latino elected to that position she has built a reputation as an independent voice and has consistently focused on issues like affordable housing public safety health care access and community representation drawing from her personal experiences with poverty and homelessness pretty sad very sad that a female felon with a 20-year criminal history is used to support uh you know this whole uh thing that's going on one thing i've learned is that shame has never changed anybody So you can't shame people, especially when they're stuck and they just spew out hate and diversion and distraction and all that stuff there. She's a Lancaster resident with a documented criminal history spanning roughly 15 to 20 years. Her record includes serious convictions. She was charged with second-degree felonies for assaulting two Lancaster police officers, kicking one, hitting another with a belt, and spitting on both, stemming from an incident where she smashed a man's car after a personal dispute. Her convictions include drug offenses, retail theft, harassment, and in 2022 she was convicted of a felony right and related charges tied to the 2020 protest ds supporters as you know value her for her honesty transparency and dedication to lancaster residents which aligns with her documented track record of advocating for the underserved homeless and vulnerable community i was going to say you all should be ashamed but shame's never changed anybody shame don't change people uh like the gentleman said take it to the ballot take it to the ballot and um we have really serious issues here in lancas ...

<sub>[context after, speaker SPEAKER_17: from the first list, Edry Dennison. I just want to confirm he's not in the room. Okay. At this point in the meeting, we don't have a legislative agenda, so this ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 138

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_06`  |  3979.0s-3996.12s  |  58 words

<sub>[context before, speaker SPEAKER_10: So applicants willing to give the city those documents.]</sub>

**TARGET --**

> Yes yeah we can provide those. And just to give a quick summary we were actually really pleasantly surprised during our due diligence period of what the testing showed. It's very very minor very small area and it's very minor. So yeah the contamination that we need to be removed is not something that we were concerned with.

<sub>[context after, speaker SPEAKER_10: okay that's good um talking about the buildings themselves and i don't know if you have anything to say to this mr smith because this would now be your kind of  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 139

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_04`  |  13472.73s-13545.68s  |  197 words

<sub>[context before, speaker SPEAKER_19: i will i will defer to betsy but first i will also say that i would not i would not characterize characterize it as the city is in favor of more use of property ...]</sub>

**TARGET --**

> thanks lauren um yeah so we did a pretty in-depth analysis of looking at a variety of different options for how big of a parcel it would be would be considered a good idea for that indoor self-storage especially is the current trend right now we anticipate that we would get more applications for it um currently our ordinance allows this type of use at 20 000 square feet or less in the r3 and r4 and as part of this ordinance we're getting that removed that's that's how the self-storage ended up in this sycamore ridge plan because they just went through the special exception process um i understand your your comments about going through the special exception process i think generally my analysis since i've started here is that we have a lot of things that require a special exception that maybe don't necessarily need to have a special exception which just increases the volume that zoning hearing board gets so i think if we have the correct standards that are in place then if they wanted to do something different they could go through that process and part of those correct centers is a

<sub>[context after, speaker SPEAKER_05: minimum acreage according to what i'm reading correct this what we're looking at is a minimum acreage correct yeah that's correct so it's not like somebody's go ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 140

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_09`  |  8763.44s-8955.91s  |  484 words

<sub>[context before, speaker SPEAKER_07: yeah and i just want to piggyback on that because i have been asking the mayor since she first took this position um that my concern was reservoir park we talke ...]</sub>

**TARGET --**

> this is a master planning effort it's not the design effort the master planning effort means reaching out to the local community to adjacent neighbors to others who may may use the park for whatever reasons they might want to and identify what is of interest to them what are the space requirements for that what are the noise implications of some of that are there aspects of the Parks and Recreation Open Space Master Plan that need to be recognized because it because it is such a centrally located park in principle because it has special characteristics such as being available as a fairgrounds type park where no other park in the city has that availability without making major damage how does one make use of that and so similar to the processes that got us from conception to more detailed design for Southend Park and others it would be inviting the community at whatever level to come in and describe what's important to them what's interesting to them hopefully it would be a series of meetings so that people can share their ideas and the consultants would come back several times to say this is what we heard you say is this what you what you actually mean and how do we put something that takes up this kind of space which might be a ball field adjacent something that takes up this kind of space which might be a skate park if those are the types of things that in consensus that community believes are appropriate so the master planning effort is to is to generate the ideas as you as you're talking about because you've presented several different ideas and many other people may have other ideas as well that they think may be appropriate for them and their their own families but it would not be the specific design it would be making sure that here are programmatically ways that these kinds of spaces can fit in this kind of a location I do want to say that it will be done a bit later in the process than the anticipated schedule for the for the south end for the east end smal ...

<sub>[context after, speaker SPEAKER_00: southeast plan, we are aware that the prison and reservoir is in the southwest, correct? So when we're asking for a plan for the southeast of Lancaster, we're n ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 141

*City Council Meeting - March 11, 2025*  |  speaker `SPEAKER_34`  |  5040.47s-5059.8s  |  38 words

<sub>[context before, speaker SPEAKER_29: i was having trouble hearing them thank you noted any additional comments on the ordinance for first]</sub>

**TARGET --**

> reading good evening hi my name is lucas i live in the 400 block of west marion uh just so the public has knowledge of where to find this uh where could we look at these ordinances before

<sub>[context after, speaker SPEAKER_29: next meeting all of our proposed legislation and proposed resolutions are listed on the city website under city council if you go to the top across the top it s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 142

*City Council Budget Hearing - November 18, 2025*  |  speaker `SPEAKER_00`  |  4600.36s-4612.24s  |  37 words

<sub>[context before, speaker UNKNOWN: related to the Bureau of tourism and promotion so we're diving into that a little bit more we'll be working closely with the advancement team the second part of ...]</sub>

**TARGET --**

> that we've invested into that we've already just started to have some preliminary conversations about what's going to be the approach and what does that look like and so it's been really excited with Kristen that's Kristen

<sub>[context after, speaker UNKNOWN: Simon, who's our new Bureau Chief of Tourism Promotion, led all of the fundraising efforts with Penn Medicine Park.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 143

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_01`  |  10366.34s-10378.57s  |  32 words

<sub>[context before, speaker SPEAKER_08: weren't made aware of that at Planning Commission okay I will just say that you know we are planning to bring the first tranche and I think Councillor Mead repo ...]</sub>

**TARGET --**

> change the process just yet and pausing this three months we we need to have bigger community community conversation about the idea of changing these public processes thank you that's what we're

<sub>[context after, speaker SPEAKER_07: we're here for. Thank you. I just want to add, I just want to add real quickly, there are non-profit organizations such as churches, multiple, a substantial amo ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 144

*Press Conference - Data Center Community Benefits Agreement*  |  speaker `SPEAKER_00`  |  1956.36s-1959.18s  |  9 words

<sub>[context before, speaker UNKNOWN: If they go lower than 80%, that's one payment. If they go lower than, I'm sorry, lower than 100, 280, and then from 60 to 79.]</sub>

**TARGET --**

> But if they fall below 60%, they're not operating.

<sub>[context after, speaker UNKNOWN: Okay. Obviously, I'll work with you.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 145

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_30`  |  1831.38s-1997.22s  |  509 words

<sub>[context before, speaker SPEAKER_18: All right. May I be in? Okay. My name is Sarah Eder Inahosa. I live in the 400 block of West Frederick. I grew up in Lancaster. I'm from the local Strong Towns  ...]</sub>

**TARGET --**

> so much for listening thank you hi my name is reagan layman i live on the 500 block of north shipping so thank you to the planning commission oh i don't think that's for me closer to the mic all right i'm not used to mics it's all good um thank you to the planning commission for the opportunity to speak on this issue because frankly i was outraged to hear about the ai dana centers planned for our community we only need to point to other cities across the country to see the impact of these data centers they strain local resources and leave communities to bear the environmental fallout just a few of the reports that i personally found when researching this for instance core reef's construction of a data center in denton texas is anticipated to use twice the city's current power usage and i believe that's on the low end low end to fuel its demand for electricity we've heard of just in the last speaker similar calculations for our city and for our county so what happens when the electric is like we have blackouts or brownouts in our communities in memphis tennessee one data center contributes to more air pollution than the oil refinery and gas powered manufacturing plants in the same neighborhood local residents have testified how much this has made it more and more difficult to breathe and given the air quality in lancaster county i don't think we are racing for the number one position of worst air quality and thirdly in granbury texas the noise pollution from fans cooling data centers have come with side effects according to time magazine residents have reported migraines nausea hearing loss and inability to sleep i don't want to see our city added to the growing list of cities impacted by data centers we never we have an opportunity to stop this impact on our community before it is too late so the demands are one the planning commission must issue an ordinance that covers the zoning of data centers as separate than warehouses and rescind the decision to zone the harr ...

<sub>[context after, speaker SPEAKER_02: promises of corporations thank you i yield my time thank you so in our demo i live in the 100 block of woodcrest drive just outside of uh just a whisker outside ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 146

*City Council Meeting - September 9, 2025*  |  speaker `SPEAKER_09`  |  4936.9s-4946.58s  |  19 words

<sub>[context before, speaker SPEAKER_03: Thank you. Additional comments from counsel on the application the resolution from the public on the resolution. Here now Mr.]</sub>

**TARGET --**

> Harris Mr. Mennon aye Mr. Roya aye Mr. Brees aye Mr. Craig aye Mr. Hirsch aye President Baker aye

<sub>[context after, speaker SPEAKER_03: thank you so much thank you our next item another local shares account application authorization is resolution number 62 2025 Mr. Harris a resolution of the cou ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 147

*Planning Commission Meeting - September 17, 2025*  |  speaker `SPEAKER_10`  |  13806.0s-13877.82s  |  122 words

<sub>[context before, speaker SPEAKER_16: like allowing making it easier to do this kind of thing and even in the cm districts i think that]</sub>

**TARGET --**

> they should be permissible but i think that they should kind of be like last resorts and i i can understand your point about the zoning hearing board having a huge load um but hopefully we can reduce some of that load with the overall comprehensive plan updates that we need to make i would take great reservation with approving self-storage by right in these zones but i do agree with eliminating it in the r3 and r4 any further comment i think the commission should consider a motion to maybe table this so that more like individual retrospection can be done about it but i can't make that motion so that's why i'm saying that how's the city what's the city's

<sub>[context after, speaker SPEAKER_04: stance um we went through several iterations of this draft ordinance to get it to the point where it's at and so at this time the city's in support of it so i g ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 148

*City Council Committee Meeting - April 1, 2025*  |  speaker `SPEAKER_13`  |  10714.3s-10719.14s  |  10 words

<sub>[context before, speaker SPEAKER_07: Just one quick question. November 18th through the 19th, is that like a marked date representing anything in the history of Puerto Rico that we can raise it on  ...]</sub>

**TARGET --**

> Councilor Arroyo, this date was chosen for a particular reason?

<sub>[context after, speaker SPEAKER_02: Yeah, typically that week is considered National Puerto Rican Week.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 149

*City Council Committee Meeting - September 16, 2025*  |  speaker `SPEAKER_06`  |  1807.99s-1826.66s  |  56 words

<sub>[context before, speaker SPEAKER_04: you which we haven't done in recent and at least during my time on council because we've operated under the same rules but this would allow us to if we wanted t ...]</sub>

**TARGET --**

> If I may the only question I have is for example if someone is coming in late and it's a constituent and by having the public comment in the beginning but not at the end when that hinder on some of the people that do work late and come to the meetings at a later time.

<sub>[context after, speaker SPEAKER_00: Well again there's never going to be perfect right so perfect can be the enemy of good. One thing I would note is it's going to depend on how council determines ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 150

*City Council Meeting - August 12, 2025*  |  speaker `SPEAKER_29`  |  3850.6s-4007.87s  |  385 words

<sub>[context before, speaker SPEAKER_07: harris our next speaker please our last speaker is tony dastra good evening it's an evening]</sub>

**TARGET --**

> uh tony dash's 700 block in new holland avenue so what i signed up to talk about was actually parking um but i'm going to connect these two issues because you have some issues that web out over time the city has a parking issue it depends on how you look at it in what perspective that issue is maybe the city is implementing positive changes for safety and it's taking away your perceived parking so you now feel left out maybe the city isn't doing enough about the parking situation maybe you feel like your parking isn't protected you need a residential zone there are wicked problems in our community that have gone poorly addressed for decades this really isn't solely on you guys this is councils before you administrations before you but right now we're looking at a problem with the data center i won't belabor details because i've said a lot about it i had feelings at the planning commission meeting but we're looking at one big issue that the public is looking for y'all to act on to say something on and i understand that you may need to ask questions of professional advice on what you can and can't do but it has been a month you're kind of speaking volumes by not saying much at all i agree with a lot of the the sentiments in this room um i'm very disappointed in this government i appreciate to the prior comments because unfortunately we want to demonstrate that we can have a good local government why because the top needs to mirror the bottom and right now unfortunately the behaviors of not just this body but bodies across this country are mirroring the top it's the marketing is better we have a comprehensive plan that still i here we finally put the rfp out for but y'all really need to ask the planning commission to act on this and y'all need to do something yourselves as well you need to speak out you need to people need to see that you're aligned in the regulation of this development because the damage it can do will affect us for generations to come much like the i ...

<sub>[context after, speaker SPEAKER_11: when their names were called. I'm gonna call them in the order which they were on the list. Darryl Lagasse. That's me. Yes.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 151

*City Council Meeting - June 10, 2025*  |  speaker `SPEAKER_00`  |  563.36s-782.48s  |  440 words

<sub>[context before, speaker SPEAKER_04: One moment. any special trick, DJ, that we need for, thank you. Thank you.]</sub>

**TARGET --**

> Oh, I know the technology now, so good. My name is . I'm a resident of Lancaster City. I live in Coral Street. I am US citizen. I'm a former refugee. I want to thank Lancaster that they've been supporting for refugees and immigrants when sometimes it doesn't feel safe to be called refugee or immigrant. We all know now that current administration, it's keep attacking the name of refugee and immigrant. We know what is happening in Los Angeles, in California. We know what is happening around us. As a former refugee, I still don't feel that I overcome anything. I remember me coming here to celebrate my citizenship. Does this matter for now for me or that can be taken away? Some refugees and immigrant communities are feeling scared and worried for what is happening right now. I want to thank city of Lancaster to pass the resolution to recognize the contribution of refugee and immigrant in economically, culturally, socially, and everything. However, we need to see elected officials making statement that refugee are safe here and immigrants are safe here and they're welcome and to highlight their contribution. We know we pay taxes, we know we work, we know we're social worker, we know we are health ed worker and give care for the people who really need it. We are in every field. We perform as American. Accept the document. We have ability. We are just a human who can do everything, who dream and who want to achieve. We want to see elected officials highlighting that because the anti-immigrant, anti-refugee rhetoric or speeches which are very discouraging and concerning. We would like to see, as you have been very welcoming, very thankful for Lancaster City administration, how they have been passing some policies to protect us. However, we need you more now. I'm with people here from the community who want to come and sit here, want to feel hope that they belong here, and they're very happy to be here. That's my dad in between. That's the community leaders from female who p ...

<sub>[context after, speaker SPEAKER_05: Thank you, Council President. I believe Zaira from the City Language Access Program is also going to be speaking.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 152

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_23`  |  5718.14s-5801.34s  |  191 words

<sub>[context before, speaker SPEAKER_12: from I'm gonna actually just introduce you to Jen Arantes who is our development manager and she handles all the LSA grants so she's gonna give you a]</sub>

**TARGET --**

> wonderful perfect again I'm Jen and the purpose of the statewide LSA program is to reinvest gaming funds into projects in the communities to improve quality of life across Pennsylvania so specifically these grants range anywhere from twenty five thousand to one million dollars and there's no local match required funding can be used to support public infrastructure community facilities equipment vehicle purchases demolition and planning and design work so a lot of the benefits that comes to the communities that apply and receive LSA funding it brings outside investment into projects that might otherwise be unfunded improves neighborhood facilities and services and creates opportunities for partnerships specifically because the city needs to apply for any nonprofits or other organizations who are interested in THESE PROGRAMS SO SINCE 2022 WHEN WE WERE FIRST ABLE TO APPLY FOR THESE GRANTS WE AS A CITY HAVE SUBMITTED 30 APPLICATIONS 11 HAVE BEEN AWARDED AND WE'RE STILL WAITING FOR 2024 APPLICATIONS IN TOTAL LANCASTER CITY HAS RECEIVED 5.9 MILLION IN AWARDED DOLLARS THROUGH THE LSA PROGRAM AND IN 2025 WE'RE EXPECTING TO SUBMIT 11 MORE THANK YOU SO MUCH ARE THERE ANY QUESTIONS FROM

<sub>[context after, speaker SPEAKER_22: THE COMMITTEE ON THE LOCAL SHARES.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 153

*City Council Meeting - October 28, 2025*  |  speaker `UNKNOWN`  |  2106.3s-2110.94s  |  19 words

<sub>[context before, speaker SPEAKER_00: are coming to put this money in the community there's no guarantee that our well-being is going to be protected and so i'm i'm at a loss for words because these ...]</sub>

**TARGET --**

> exclusively not the mayor all of us are in this we are all stakeholders in the city of Lancaster

<sub>[context after, speaker SPEAKER_00: and any legal fight we want to have and unfortunately this has gotten to the territory where we are definitely going to have a legal fight of some kind and we w ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 154

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_11`  |  6511.91s-7233.92s  |  1685 words

<sub>[context before, speaker SPEAKER_22: with a quick little install don't forget to hit your button there you're going to spread]</sub>

**TARGET --**

> good evening everybody sorry for the delay i was looking for my speaker notes but we're going to go with plan b and use the hard copy instead um okay um well uh thank you for the opportunity uh to speak on this topic tonight i know there's been a lot of interest in data centers overall um and particularly uh subject of zoning um uh first uh i think all of you know me i'm chris delfs i'm the director of community planning and economic development uh but wanted to introduce myself again um for uh public in the room as well uh also wanted to turn it over just for a moment so that uh betsy can introduce herself as well good evening i'm betsy logan i'm the planning bureau chief for the city okay um i think i'm going to do most of the talking but um betsy's the technical expert here in a number of the these areas so she may assist with some parts of the presentation and answer uh questions as well um okay uh should we jump in absolutely good okay um just wanted to start with with where we've been uh on august 26 city council directed staff and the solicitor's office to develop a zoning ordinance to specifically address data centers in the city of lancaster our chief planner betsy who you just met and i have been working on the draft ordinance since that time in august in concert with our city solicitor and also we have outside land use council that we use for important matters such as these during that time we've researched best practices we've spoken to experts we've connected with other other municipalities, and generally attempted to build our knowledge about data centers, both their challenges and their opportunities. Please note, this is the first draft of the ordinance, which will undergo additional rounds of review and feedback. So normally, I end a presentation with process. I don't usually start with process, but I think in this case, it's really important. So we're clear about where we're headed. formulating zoning code was designed to be deliberative in other w ...

<sub>[context after, speaker SPEAKER_21: questions at this time okay so my question is related to the noise is there like i know that they have decibels levels um and i'm not sure the acoustic i'm thin ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 155

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_03`  |  3104.71s-3116.6s  |  15 words

<sub>[context before, speaker SPEAKER_09: the pictures that I put up there you can see what's happening to that loading]</sub>

**TARGET --**

> zone I mean have people sleeping on the ground okay okay okay thank you very

<sub>[context after, speaker SPEAKER_04: much thanks thank you for your time so we haven't created a motion to have the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 156

*City Council Meeting - April 29, 2025*  |  speaker `SPEAKER_11`  |  4782.93s-4803.6s  |  54 words

<sub>[context before, speaker SPEAKER_03: evening hello my name is taylor raymond i live on the 500 block of saint joseph street and i'm here for something not regarding ms diaz at all at previous meeti ...]</sub>

**TARGET --**

> thank you good evening good evening thank you for your time my name is ashley and i lived in lancaster for the past 16 years i'm here today to proudly support janet diaz i want to start by saying something important i hear your frustration i understand the pain ashley i'm sorry i don't

<sub>[context after, speaker SPEAKER_17: know your last name can you just say your full name oh yeah ashley martinez thank you appreciate]</sub>

`public_comment:` ____   `note:` ____

---

## Item 157

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_09`  |  2030.25s-2042.99s  |  27 words

<sub>[context before, speaker SPEAKER_05: request was withdrawn at the meeting and it looks like in the intro there's been a new request that was handled administratively for a handicapped parking spot  ...]</sub>

**TARGET --**

> So you're putting the loading zone that people use on Lemon Street so when the purveyors that go to the Belvedere, they have to cross two intersections

<sub>[context after, speaker SPEAKER_04: now. Well, it's to be put in a location that tries to serve as many businesses as possible.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 158

*City Council Meeting - May 27, 2025*  |  speaker `SPEAKER_05`  |  5303.12s-5327.63s  |  73 words

<sub>[context before, speaker SPEAKER_09: Sirachi our next item is the report of president of council I don't have a specific report but I wanted to thank you for highlighting the work that our students ...]</sub>

**TARGET --**

> council tonight council president if i may counselor i just wanted to make the other members of council aware that the home rule study transition committee did meet on may 6th and went over both the administrative code as well as the ethics code which will be which we are currently doing the interviews for and will be more to come but we are on track and we are on time and that

<sub>[context after, speaker SPEAKER_09: concludes my report thank you very much counselor med i will also just to backtrack a little bit because you mentioned that i will mention to members of council ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 159

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_09`  |  3061.27s-3063.87s  |  13 words

<sub>[context before, speaker SPEAKER_04: You had said that there were loading zones where there were no businesses.]</sub>

**TARGET --**

> Yeah, it's no business there. It's closed. It's been closed for two years.

<sub>[context after, speaker SPEAKER_03: Okay, what's the set up?]</sub>

`public_comment:` ____   `note:` ____

---

## Item 160

*City Council Meeting - March 11, 2025*  |  speaker `SPEAKER_17`  |  8372.27s-8396.52s  |  35 words

<sub>[context before, speaker SPEAKER_29: Are there any further comments for the second]</sub>

**TARGET --**

> period? Taylor Raymond again 500 block of St. Joseph Street. Is it normal for the mayor and the chief of police to be at these meetings? Is this an unusual circumstance that they aren't here?

<sub>[context after, speaker SPEAKER_29: The chief of police normally doesn't attend regular meetings unless there's a report that's been requested like we were talking about earlier. The mayor typical ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 161

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_28`  |  6428.68s-6446.08s  |  26 words

<sub>[context before, speaker SPEAKER_09: and we have a second ready for the question uh since we have to be specific in this as a com a question i believe we should also have the mayor there as well]</sub>

**TARGET --**

> okay i again i'm not a legal expert but i don't know what the planning commission's powers are to demand that people attend this public hearing

<sub>[context after, speaker SPEAKER_17: so we can't request that as as much you can certainly invite you could definitely invite i don't know that you can require i don't know okay invite yeah i mean  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 162

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_20`  |  9260.06s-9300.26s  |  108 words

<sub>[context before, speaker SPEAKER_28: we exhausted all the possibilities to the rear of the parcel and there for a variety of reasons the inability to provide safe egress so we have spent you know a ...]</sub>

**TARGET --**

> which is for affordable housing counselor uh this is a quick question um i know that it was quoted that the land development cost to build the park would be around 600 000 is that current or i mean that could also rise with increased costs um so if the administration has a ballpark figure what i know this is a very challenging piece of land i also understand the community member who spoke out tonight's frustrations but at the end of the day i mean this is going to cost hundreds of thousands of dollars to develop in unbudgeted costs so the administration just speak to what

<sub>[context after, speaker SPEAKER_28: the current cost would be to develop the park i do not have a current estimate that estimate was from 2023 is and director campbell's shaking his head yes so 20 ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 163

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_25`  |  5029.04s-5157.76s  |  318 words

<sub>[context before, speaker SPEAKER_30: THAT I WOULD RECOMMEND CONSULTED GREG TO TABLE THIS FOR NOW UNTIL YOU AND YOU GUYS AND THE HISTORICAL COMMISSIONS FIND A COMMON GROUND ON THAT THANK YOU YEAH GO ...]</sub>

**TARGET --**

> CRAIG I JUST WANT TO MAKE A COMMENT BECAUSE THIS VERY INTERESTING SITUATION THAT WE'RE IN SO when i want to be empathetic to the fact that uh it was mentioned that clerical error was made so i have um it's a little frustrating to feel that we're going to put the onus on a property owner uh to um a resident to have to correct that when uh it was something on our process that potentially could have prevented this um the other thing that i do want to mention why i think there i have a deep appreciation for our city's historical infrastructure i think the reality as well is that there are numerous conversations that are happening throughout our community around housing affordability energy consumption energy affordability and it's going to take innovative solutions to solve those challenges so um right now we have this tension between a historic housing stock uh which you know yes we we definitely should preserve and um also the need for innovation innovative solutions around housing affordability uh so it's interesting that this specific property um also is demonstrating this new idea that can save anywhere from 70 to 90 in energy costs which i find fascinating for a city that is suffering through a housing crisis and housing excuse me a housing affordability crisis and energy consumption can be um a big part of that so um yeah i just i want to make that comment i think uh given the fact that this is done i would also uh encourage and recommend mayor sirachi's recommendation around tabling this uh to ensure that you know we can come up with a good solution and move forward that honors um our CITY'S HISTORIC INTEGRITY BUT THEN ALSO UNDERSTANDS THAT YOU KNOW THERE ARE OPPORTUNITIES FOR NEW INNOVATIVE SOLUTIONS TO HOUSING AFFORDABILITY HERE THANK YOU COUNCILOR THANKS ARE THERE ANY

<sub>[context after, speaker SPEAKER_13: QUESTIONS OR COMMENTS FROM THE PUBLIC THIS IS ON OKAY IT'S ACTUALLY AT MY LEVEL I'm Susie Hoover I have a house at 204 East King Street 1787 when I redid that h ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 164

*City Council Special Meeting - November 20, 2025*  |  speaker `UNKNOWN`  |  7462.23s-7466.47s  |  16 words

<sub>[context before, speaker SPEAKER_00: Together, we as economic development organizations focused on the city and the county support the adoption of the Lancaster AI Hub Community Benefits Agreement. ...]</sub>

**TARGET --**

> respectfully urge you to approve the community benefits agreement and we are here to support you

<sub>[context after, speaker SPEAKER_00: thank you for your time and consideration thank you good evening tony dastro 700 block new holland]</sub>

`public_comment:` ____   `note:` ____

---

## Item 165

*City Council Committee Meeting - November 3, 2025*  |  speaker `SPEAKER_00`  |  4885.56s-4904.53s  |  46 words

<sub>[context before, speaker UNKNOWN: we were told for this year was that we could expect it to go anywhere from eight months to I think it's been a year and two months before so they were hopeful t ...]</sub>

**TARGET --**

> Sure. Great. Thank you for that. That ambiguity is tough because prices for these projects keep going up and up and up, and you apply a year and a half ago, and now you're back again. I feel your frustration. Okay. All right. I will make

<sub>[context after, speaker UNKNOWN: a motion to move this application resolution number 74 to full council on the 11th second all those in favor aye thank you so much yeah thank you all we are now ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 166

*City Council Meeting - June 10, 2025*  |  speaker `SPEAKER_10`  |  4188.98s-4203.88s  |  28 words

<sub>[context before, speaker SPEAKER_03: the resolution there's Gomez I just want to piggyback on what Irene said yes there's lots of residents being delayed ignored and denied my father in particularl ...]</sub>

**TARGET --**

> resolution mr. Dastra 700 block New Holland Avenue I just want to thank mr. Arroyo for being transparent about the refusal and I look forward to seeing the

<sub>[context after, speaker SPEAKER_04: submitted thank you thank you any additional comments from the public]</sub>

`public_comment:` ____   `note:` ____

---

## Item 167

*City Council Budget Hearing - October 21, 2025*  |  speaker `SPEAKER_00`  |  2422.65s-2436.25s  |  34 words

<sub>[context before, speaker UNKNOWN: but did not have the dedicated resources to do that and what we find is that we we have a lot]</sub>

**TARGET --**

> of training that we need to be doing internal to the organization um related to hr man and management um people are complicated it turns out so this is a recommendation that is literally

<sub>[context after, speaker UNKNOWN: two plus decades in the making and i'm strongly supporting it it was recommended in 2007 so thank you my second question I'm not sure if it should wholly go to  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 168

*Planning Commission Meeting - October 15, 2025*  |  speaker `UNKNOWN`  |  1080.0s-2181.45s  |  4 words

**TARGET --**

> Thank you. Thank you.

<sub>[context after, speaker SPEAKER_00: Thank you.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 169

*Traffic Commission Meeting - November 11, 2025*  |  speaker `SPEAKER_00`  |  2754.03s-2757.59s  |  16 words

<sub>[context before, speaker UNKNOWN: we're looking at and i i've never seen it that empty which is which is great maybe it's a sign of the future but um what i've been noticing is the cars from nor ...]</sub>

**TARGET --**

> four-way stop is the answer that's just one of the things I put in my note

<sub>[context after, speaker UNKNOWN: somehow I'd like to see attached to the stop sign something that alerts people someone else yes does anyone else want to speak to this item as well please come  ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 170

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_09`  |  2962.56s-2992.67s  |  79 words

<sub>[context before, speaker SPEAKER_02: answer that question here but why why is neither block from this block there's no setbacks. So on North Queen Street. So you're parking within 20 feet of a cros ...]</sub>

**TARGET --**

> Street? First to get what on Queen Street? The setbacks. The pavement markings and the delineators? The pavement markings. The pavement markings and the posts? I guess the posts haven't gone in. No, on the streets. I mean, we've done it on many intersections throughout the city. I don't know of any. On Chester Street, it's right up to the crosswalk and following block and James Street, it's up to the crosswalk. I mean, it's more than every location.

<sub>[context after, speaker SPEAKER_02: It's, you know, it's part of the vehicle code. So we try to emphasize it at certain locations by putting those paper markings down.]</sub>

`public_comment:` ____   `note:` ____

---

## Item 171

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_00`  |  12964.64s-13148.9s  |  451 words

<sub>[context before, speaker SPEAKER_20: it is there a second to councillor hirsch's motion i seconded it i think you'll call the vote this is this is your committee so you may call a vote all in favor ...]</sub>

**TARGET --**

> so thank you very much this is an opportunity for us to make sure that arpa funds that were designated for one purpose can be continue to be used for a very similar in in line purpose um so the change in use for the arpa plant for the arpa funds is granted to the lancaster recreation commission for renovation of the price elementary school we are wanting since since lancaster rec has determined that they're not going to go forward with with price we want to be able to spend the remainder of the arpa dollars on other aspects of the renovation of the length existing lancaster facility which include hvac refurbishment of the elevator and refurbishment of the of the the structural bridge that the entrance bridge if there are sufficient funds the funds that had been allocated to from arpa were 750 000 uh we believe that there's about three hundred and seven thousand dollars left however both uh lancaster rec and sdol are confirming what has and has not been spent on the price building for not only asbestos abatement but for structural purposes we have reasonable estimates that the hvac which which dpw in the city of lancaster have been hobbling along with for the past two or three years with just window units can be performed for for under three hundred thousand dollars so if there is remaining three hundred seven thousand dollars and in then we can get the hvac done to everyone's satisfaction if we get better bids then we can go into the into the elevator which is a which we're estimating to be about 95 to 150 000 to do the elevator um and that's because the elevator has is several years beyond its remaining useful life and as a facility that is used by these seniors as well as a wide variety of individuals having handicapped accessibility throughout the facility would be very, very important. If we can only use the 307,000, if there's only 307,000 left, that's wonderful as far as we're concerned and we will continue through the facility condition assessment process to  ...

<sub>[context after, speaker SPEAKER_20: director campbell um being well acquainted with the needs of that building i appreciate that we were going to be able to to move those funds into this purpose s ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 172

*City Council Committee Meeting - October 6, 2025*  |  speaker `SPEAKER_06`  |  8813.67s-9001.97s  |  521 words

<sub>[context before, speaker SPEAKER_15: see a single story of a community glad to have them i think we should sit and think on that]</sub>

**TARGET --**

> thank you mr dastran how you doing wonderful tony dash at 700 block of new holland avenue i will do my best to keep this one positive uh because i'm very glad to see this ordinance director delfs it is way more robust than i honestly had been anticipating so i appreciate the reviews you've done of all the documentation you've been provided by the public um i do have some notes and i also want to thank you for your calling out of the good faith that was one of the things i underlined as soon as i read this um so moving on from the good faith that will definitely come up later in other agenda items but i want to encourage the council to change it from special exception to conditional use especially in light of not having an updated zoning amendment right now this is working in between where we need to get with our comprehensive plan and what where we're at right now so I think the most acceptable thing for the public would to be having conditional uses because as these data centers move through our community it holds this body directly accountable to what products are approved in addition of that I believe under electronic waste mr. Arcolio has persuaded me that we need to have a bond to guarantee that those plans get enacted and that should be outlined explicitly in those electronic waste plans with a bond as far as water utilization goes I do believe there's a way for us to draft agnostic legislation because industrial use of water not just for data centers but other facilities is something that is a very real impact for our community potable water where it's available especially in a community a a community like ours that is dependent on rainfall to dilute the, what are we calling them, PFAS in our water, it's critical that we save every drop of potable water we have. So they shouldn't be going to just cooling uses. If something's not producing a consumable product by humans, animals, or otherwise agricultural use, I think we need to eliminate that. Yeah, I mean, h ...

<sub>[context after, speaker SPEAKER_08: thank you mr dastra um there you go you knew i'd be up here frank garcolio uh old trinity place uh yeah so uh i have to say that this is a lot better than i exp ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 173

*City Council Meeting - February 11, 2025*  |  speaker `SPEAKER_01`  |  974.99s-1045.73s  |  185 words

<sub>[context before, speaker SPEAKER_09: this is coming through public works councillor hirsch thank you council president um this]</sub>

**TARGET --**

> resolution is essentially uh entering the city into a cost-sharing agreement with maynham township as many of you may know marshall avenue is along the northern border and southern of the city and the southern border of man i'm township um and it zigzags pretty chaotically and so this kind of allows the city to enter into an agreement where um they are taking on the portion of the cost that uh is proportionate to the city's ownership of the road which in this case these improvements are primarily going to be to improve uh biking and walking infrastructure along marshall ave total cost is roughly 62 000 so it's a pretty low cost project on the whole the city is going to take 82 percent of that as they own 82 percent of that roadway it's not a full resurfacing project it's base improvements to the roadway to allow the additional infrastructure to be put in and my understanding is that the work is slated to take place later this year it's a correct director Campbell is nodding so that's pretty much the deal

<sub>[context after, speaker SPEAKER_09: with with this room thank you very much council Hirsch I'll just say whoever figured out that we owned 82% specifically of the road at kudos to them spent a lot ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 174

*Traffic Commission March 11, 2025*  |  speaker `SPEAKER_04`  |  2746.0s-2753.49s  |  17 words

<sub>[context before, speaker SPEAKER_02: should we do another assessment yes and identify so i think if that's the case then it could be handled like a typical loading zone in that you're identifying i ...]</sub>

**TARGET --**

> loading zone and it would still be a handicap parking space correct that is that that has

<sub>[context after, speaker SPEAKER_02: been installed and i believe it's on the consent agenda that has been installed the handicap yes]</sub>

`public_comment:` ____   `note:` ____

---

## Item 175

*Planning Commission - August 6, 2025*  |  speaker `SPEAKER_11`  |  7679.58s-7715.06s  |  59 words

<sub>[context before, speaker SPEAKER_15: logic is making sense for why it would be deferred i have a question do we know if there's a sidewalk]</sub>

**TARGET --**

> on the other side of manheim pike no there's not i have maybe two comments more than a question with the um no they are both questions i apologize the is there a bus stop in front of yale that i'm not sure i was trying to zoom in a little bit to see if i can see it

<sub>[context after, speaker SPEAKER_25: oh good you have it even better on yours thank you um okay so my biggest concern i echoing a little bit of this i agree manheim pike right now it]</sub>

`public_comment:` ____   `note:` ____

---

## Item 176

*City Council Meeting - April 8, 2025*  |  speaker `SPEAKER_08`  |  5789.01s-5797.38s  |  14 words

<sub>[context before, speaker SPEAKER_07: resolution 31 from the public Darlene Byrd I heard you say on the other one for South End Park that you were looking for a match from other grants does this req ...]</sub>

**TARGET --**

> resolution 31 it's coming from the 2025 bond funds that were just approved thank

<sub>[context after, speaker SPEAKER_07: you so we already borrowed the money for the match for this project through the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 177

*City Council Committee Meeting - September 16, 2025*  |  speaker `SPEAKER_05`  |  3173.06s-3188.8s  |  44 words

<sub>[context before, speaker SPEAKER_04: have been canceled thank you yeah I am seeing them on the website here the next one that's listed because I can see future dates is September 25th here in]</sub>

**TARGET --**

> polite council chambers thank you well actually I do have the cancellation from I believe that was in August and there was one in July that they were both canceled and I know that because I came personally and was told it was canceled

<sub>[context after, speaker SPEAKER_04: and being rescheduled i don't have any i don't have any of that information but thank you are there any additional public comments on this section of the admini ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 178

*City Council Meeting - June 10, 2025*  |  speaker `SPEAKER_03`  |  4042.1s-4188.98s  |  322 words

<sub>[context before, speaker SPEAKER_04: questions thank you miss Grievous to answer your question a couple things the critical repair program isn't comprised of millions of dollars it's a few hundred  ...]</sub>

**TARGET --**

> the resolution there's Gomez I just want to piggyback on what Irene said yes there's lots of residents being delayed ignored and denied my father in particularly who is an owner-occupant and me myself we are not given the opportunity nor irene but several of her issues and no she did not say that it was millions of dollars because you guys are very specific about taking little things out of context it's the concerns the issues that current residents homeowners continuously have whether it's more taxes more dollars and programs or funding being given to outsource outsources out people that are coming in from out of town not residents that are that have been here for 30 40 you know years and we're talking about from businesses to homeowners to regular residents we come up here we stress our concerns you look at us with a blind eye and it's like we're a public nuisance why because that's how you look at us because you're feeding your deep pockets while everyone else is enjoying it but you can walk outside your neighborhood just like the gentleman said earlier tons of people sitting and he can't even go to sleep at night and he's a hard worker that's not he's he's one of major like maybe a hundred people in this city over a hundred that can share the same testimony that he shared where's the concerns for the citizens you know we all we're seeing is things being applied for investors a hotel being built when you when there's no affordable housing it's not affordable affordable housing is is meeting the medium income it's not affordable for the citizens of lancaster so stop saying affordable housing it's disgraceful for you guys to just continuously turn your eye towards hard-working citizens and taxpayers in lancaster city who are being deprived of their resources sad any additional comments from the public on the

<sub>[context after, speaker SPEAKER_10: resolution mr. Dastra 700 block New Holland Avenue I just want to thank mr. Arroyo for being transparent about the refusal and I look forward to seeing the]</sub>

`public_comment:` ____   `note:` ____

---

## Item 179

*City Council Meeting - May 13, 2025*  |  speaker `SPEAKER_07`  |  5253.16s-5278.8s  |  58 words

<sub>[context before, speaker SPEAKER_30: we have a motion and a second council craig is here intention to take them together as that right counselor med is that you're seconding that okay we have a mot ...]</sub>

**TARGET --**

> items that's a hearse can we it seems can we receive some clarity because per the letter from the hard it says that there is one application that was approved in one that was tabled until Barb's June meeting and I just want to make sure that that we have a clear understanding of which has been approved

<sub>[context after, speaker SPEAKER_02: by which before we would vote on this thank you good evening I can provide some clarification there were two items on the harp committee meeting the one that is ...]</sub>

`public_comment:` ____   `note:` ____

---

## Item 180

*City Council Committee Meeting - March 3, 2025*  |  speaker `SPEAKER_07`  |  4011.4s-4176.38s  |  490 words

<sub>[context before, speaker SPEAKER_05: thank you for the presentation this evening it's nice to meet you uh officially uh thank you could you speak a bit about i know that there are probably some res ...]</sub>

**TARGET --**

> in kind of two different ways uh the first one is process uh especially since i started i've been working with um various people within the city to make sure that we have a a good effective process for addressing these concerns like when a tree branch comes down or when someone needs to have assistance and I think we've been working very well about that we've made some significant improvements in the last month or so in parts of that and so as especially as the City Works City View programs come online that is also going to make things much easier as it will sort of very well streamline things will be all electronic we won't necessarily have to have people call in or or maybe just through like the fix it link so when it comes to making it more readily available more intuitive to get those resources I think we're going in the right direction the second part is more you know how are we addressing you know our art where our trees are placed And so one of the big things I always like to say is more tree equal more better with the caveat of the right tree in the right spot and One of the things I'm sure we all are aware of is that if we're wandering through town The sidewalk is not necessarily the most level at times. Sadly that does have to do with some of our trees That also is probably related to the fact that we have nearly a quarter of the city trees being maples historically they've been very easy to get and the plant but because of how they work in their ecosystem as some of the first ones in there they put down shallow roots they really grow them and push them out and then of course the sidewalks kind of suffer that those sorts of decisions were at the time very much like we need a tree we're gonna put something in there we are being far more systematic about that I actually just redid our citing guidelines to make sure that when there we are either planning a well or planning work around the well we're keeping in mind now the subsurface infrastructure more of th ...

<sub>[context after, speaker SPEAKER_06: good way any other question or comment from in regards to replacing some of trees do you have like specific trees that you might have found that they're disease ...]</sub>

`public_comment:` ____   `note:` ____

---
