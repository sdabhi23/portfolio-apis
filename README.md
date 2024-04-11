# APIs for my portfolio website

This repo contains the source code for the APIs being called from my personal website / portfolio website (<https://shreydabhi.dev>).

These APIs are hosted on AWS Lambda and are behind an AWS managed API Gateway. The sensitive tokens and credentials are stored in AWS Secrets Manager.

## GitHub API

The website renders a summary of a subset of my most prominent GitHub projects. The GitHub GraphQL API needs an access token. To hide this token from the internet I have created an endpoint which fetches data from GitHub and relays the data to the frontend.

## Email API

I do not like to expose my email id to the internet for the fear of being spammed. So I have created a form on my portfolio which calls an API to send the data to me over email. I have used [MailJet](https://www.mailjet.com/) to send emails programmatically.
