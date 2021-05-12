# fark

I'm a fan of Fark.com.   Lots of informative (and wacky) news stories, full of witty commentary.   And pictures!   Lots of funny pictures!   

Many years ago, I would simply save the pictures I liked one at a time.   That was ok, but I decided to automate the process and download all the pictures in mass.  
This program downloads all pictures posted to the comment sections from the forums created within the previous 7 days.  

The program expects:

- ./db/fark.db  - database used for tracking progress.  
- ./pics/       - directory to where all the pictures are download.    

I run this in Docker and BIND these two directories outside of Docker where I can access the pictures and persist the database.   

