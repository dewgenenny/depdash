# DepDash is a first attempt at creating an org-level dashboard for dependabot alerts

Dependabot is amazing! Being able to see what security issues you have on a dependencies used in your app is amazing, helping to keep on top of security issues.

However for an organisation, there is no dashboarding in Github to see what your overall exposure is.

Hence I had a go here at building something to help in that space. It queries github graphql interface for your all your orgs repos and the corresponding vulnerabilities, then pushes this to datadog for visualisation / historisation.

Code is very much PoC and brittle, but shows that it is possible.
