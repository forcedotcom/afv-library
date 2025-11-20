---
name: DateUtils Utility Primer
description: Generate a documented DateUtils Apex class with daysBetween and addDays helpers.
tags: apex, utility, beginner
---

Generate a small `DateUtils` Apex utility class. Include clear comments so I can understand the overall structure and common Apex patterns. 

Create the following two methods:

- A method named daysBetween that returns the number of days between two dates. If either date is null, return null instead of throwing an exception.
- Add a method named addDays that returns a new date by adding a given number of days to a base date. If the base date is null, return null.

Do not create unit tests at this time.

Deploy this class to my org using the Salesforce DX MCP Server.
