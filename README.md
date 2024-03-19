# BranchLibrary Project

*Ongoing project to create a site where users can collaborate with collective storytelling in an open source style of contribution.*

![Mission Statement](main.png)

## Current Database Schema
![DB Model](db_model.png)

*Below are the backlog ToDo's for desired features.*


## Backlog:
1) __Version Control System__
	- Fork Difference Comparison Summary.
	- ~~Pull Request system for content merges.~~
        - ~~PR GUI HTML & CSS Format~~
            - ~~Checkbox System~~
            - ~~Table List~~
            - ~~Theme Consistency~~
        - ~~Add PR Route to app file.~~
        - ~~added database schema for PR req.~~
        - ~~Altered "UPDATE" route in main.py to faciliate PR.~~
        - ~~Altered Update.html to show checkbox for PR.~~
    - ~~Schema for Forked Content.~~
	- ~~Content Version Directory.~~
    - ~~Make Delete action be exclusive to content owner.~~

2) __Community Features__
    - Create Account Deletion Functionality.
    - Active User Account directory[WIP].
        - Add Search Functionality
	    - ~~Added Directory of Users.~~
        - ~~Added list of Stories by user.~~
    - Integrated Instant Message system.
	- Contribution Point System.
    
3) __Text Editor UX__
	- ~~Font Selection for Editing.~~
	- ~~Style Customization.~~
	- User Themes.
	- Intellisense for text.

4) __General UX__
    - Improve routing when login, update or any other partial navigation occurs.
        - Currently users typically are routed back to index, instead route to last location prior to action.
    - When User creates new account, login new acct automatically, rather than require follow up login.

## Known Bugs:
1) ~~__Non Logged in Users can Attempt to edit a Story__~~
2) ~~Delete action in Story list does not work.~~
