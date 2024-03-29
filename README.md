<div align="center">
  <img height="300px" alt="logo" src="./app/static/logo.png">
  <br />
  <br/>
  <h1>Art Forgery</h1>
</div>

### 1- Team setup
In the `creds_sample.csv` file, you will find the format for team information as shown below:
```
University,Teams,Password
team1,izi,password
team2,potato,password
```

For each team, two accounts will be created:
```
username: izi_1     password: password    username: izi_2     password: password
username: potato_1  password: password    username: potato_2  password: password
```

To copy the credentials content to the appropriate folder, execute the following command:
```sh
cp creds_sample.csv app/creds.csv
```

### 2- Setting Up the Images
Place the images in the `app/challenges-img/` directory. Each image represents a round. The rounds are determined by the lexicographical order of the images in the folder.

### 3- Starting the Server
To start the server, run:
```sh
docker compose up --build
```

Then, navigate to http://localhost:8943.

### 4- Starting a game
Log in using the administrator account:
```
username: admin
password: SUPER_STRONG_PASSWORD
```

Participants should log in with their respective team accounts.

And when the administrator clicks on the start button, the participants receive their first forgery mission.


### 5- rules
<h4>Process</h4>
<p>Since the war, an economic crisis has emerged. Seeing that NFTs were doomed to fail (#woke), you decided to turn to an ancient, forgotten technology: the web! Armed with your expertise as a front-end architect, you plan to make a fortune by replicating ancient artworks and then reselling them in a digital format.</p>
<p>Mercenaries at heart, be vigilant! ChlorophyllAI monitors all cloud and digital transactions. Therefore, it will be impossible for you to replicate a work for more than 35 minutes.</p>
<p>Thus, in each round, you will have 35 minutes to copy the work as faithfully as possible, after which you must move on to the next one.</p>
<p>During your artistic performance, you will unfortunately not be completely free to act as you wish. ChlorophyllAI would find it too easy to spot your talent! To counter this, you will need to divide the work. After a consensus, one person will take care of the HTML while the other will handle the CSS. To avoid exhausting the participants, these roles will be exchanged with each new artwork.</p>
<p>From time to time, it is important for the two artists to synchronize their work to be able to construct the artwork.</p>
<p>/!\ Beware! Counterfeiting is an illegal act, so you will need to be discreet. When synchronizing your code with your accomplice, it might happen that an eavesdropper intercepts the communications. Therefore, during synchronization, it is possible that everyone might catch a glimpse of the information transmitted to your accomplice.</p>
<p>After each round, a short break will be granted to the artists, allowing them to review their creative process.</p>

<h4>Constraints</h4>
<h5>Artists in General</h5>
<p>Due to the nature of your mission, you must remain discreet in the face of a supreme artificial intelligence. Therefore, you cannot rely on the internets or on powerful software. You will have to work hard using an old editor specially designed not to be detected by artificial intelligence.</p>
<p>If the latter notices you due to the use of the internets or a third-party software, it will no longer be possible to become the best team of artists; your overall score will drop to zero. Favor high-voice communications, the old computers provided to you cannot be controlled by the threat, so it will be possible to speak without fear of being caught by the superior intelligence.</p>

<h5>HTML Artist</h5>
<p>Here are the restrictions regarding the tags and attributes you must adhere to. If your creative process leads you to use these elements, they will not be considered by the counterfeiting platform.</p>
<span>Forbidden tags: [script, iframe, link, img, style, embed, object, svg]</span>
<span>Forbidden attributes: [style, background, src, href]</span>

<h5>CSS Artist</h5>
<p>Here are the restrictions regarding the style of the work that you must adhere to. If your creative process leads you to use these elements, they will not be considered by the counterfeiting platform.</p>
<span>Forbidden elements: [@import, url(...), expression(...)]</span>
<span>HTML tag injection will also be removed.</span>

<h4>Synchronisation</h4>
<p>With each synchronization, the server will keep a footprint of your code. The last footprint of each artist will be used to design the final work. It is therefore your responsibility as an artist to ensure that your last synchronization is successful.</p>

<h4>Data Leak</h4>
<p>With each synchronization, there is a one in ten chance that the section requested for synchronization will be disclosed to the other artists on the platform.</p>

<h4>Scoring</h4>
<p>In each round, you will be awarded a score out of 1000 points based on the similarity between your work and the original. In the event of a tie, the length of the code will be taken into account.</p>
<p>A ranking will then be created for the round that has just ended to determine which work is most likely to copy the original. The first place will receive 22 points while the last team will receive 0 points. The artist teams between these two extremes will receive a number of points according to their score relative to these two extremes.</p>
<span>Formula for your points from a round: (x - y) / (w - y) * 22 where</span>
<span>x: your similarity score,</span>
<span>y: the minimum similarity score obtained by all the teams,</span>
<span>w: the maximum similarity score obtained by all the teams.</span>
<p>The overall score will be a sum of the scores from each round.</p>
<p>If a tie occurs, the length of the code will be deterministic to differentiate the two teams.</p>