from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import logging
logging.basicConfig(level=logging.ERROR)
from collections import defaultdict
import os
from datadog import initialize, statsd, api

from datetime import date

today = date.today()
d1 = today.strftime("%d/%m/%Y")



GITHUB_AUTH_TOKEN = 'Bearer '+ os.environ['GITHUB_AUTH_TOKEN']
DATADOG_API_KEY = os.environ['DATADOG_API_KEY']

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers={'Authorization': GITHUB_AUTH_TOKEN})


# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

# Provide a GraphQL query
query = gql(
    """
query ($cursor: String)

{
  viewer {
    repositories(first: 50, after: $cursor, affiliations: [OWNER, ORGANIZATION_MEMBER], ownerAffiliations: [ORGANIZATION_MEMBER]) {
      pageInfo {
        startCursor
        hasNextPage
        endCursor
      }
      nodes {
              defaultBranchRef{
                  target {
          ... on Commit {
									pushedDate
                }
        }
        }

        vulnerabilityAlerts(first: 100, states:OPEN) {
          nodes {
            repository{
              nameWithOwner
            	url
            }
            securityVulnerability {
              severity
              package{
                name
              }
              advisory {
                summary
                description
              }
              
            }
          }
          totalCount
        }
        name
        description
        url
        createdAt
      }
      totalCount
    }
  }
}


"""
)


def update_datadog(data):

    options = {
        'api_key': DATADOG_API_KEY,
        'api_host': 'https://api.datadoghq.eu',
    }

    initialize(**options)

    for repo in data:
        repo_url = repo[0].replace("-", ".")
        criticals = float(repo[1])
        highs = float(repo[2])
        mediums = float(repo[3])
        score = float(repo[4])
        print(repo_url.replace("https://github.com/seatcode/", "") + " - " + str(criticals) + "," + str(highs) + "," + str(mediums)) #had issues pushing data with / characters
        repo_name = repo_url.replace("https://github.com/seatcode/", "")

        critical_name = "security.dependabot.vulnerabilities.critical"
        high_name = "security.dependabot.vulnerabilities.high"
        medium_name = "security.dependabot.vulnerabilities.medium"
        total_score = "security.dependabot.vulnerabilities.score"

        response = api.Metric.send(
            metric=critical_name,
            points=[criticals],
            tags=["repo:" + repo_name],
            type='gauge'
        )
        response = api.Metric.send(
            metric=high_name,
            points=[highs],
            tags=["repo:" + repo_name],
            type='gauge'
        )
        response = api.Metric.send(
            metric=medium_name,
            points=[mediums],
            tags=["repo:" + repo_name],
            type='gauge'
        )
        response = api.Metric.send(
            metric=total_score,
            points=[score],
            tags=["repo:" + repo_name],
            type='gauge'
        )
results_list = []

# Execute the query on the transport
result = client.execute(query)
results_list.append(result['viewer']['repositories']['nodes'])


# Deal with pagination

while result['viewer']['repositories']['pageInfo']['hasNextPage']:
    print("cursor = " + result['viewer']['repositories']['pageInfo']['endCursor'])
    params = {"cursor": result['viewer']['repositories']['pageInfo']['endCursor']}
    result = client.execute(query, variable_values=params)
    results_list.append(result['viewer']['repositories']['nodes'])

vulnerability_totals = defaultdict(dict)
vulnerability_details = []

for repository in results_list:

    for vulnerabilities in repository:
        if(len(vulnerabilities['vulnerabilityAlerts']['nodes']) > 0):
             for vulnerability in vulnerabilities['vulnerabilityAlerts']['nodes']:
                 vulnerability_details.append([vulnerability['repository']['url'] ,vulnerability['securityVulnerability']['severity'], vulnerability['securityVulnerability']['package'][ 'name'],vulnerability['securityVulnerability']['advisory'][ 'summary']])
                 if not vulnerability_totals[vulnerability['repository']['url']]:
                    vulnerability_totals[vulnerability['repository']['url']] = defaultdict(int)
                 vulnerability_totals[vulnerability['repository']['url']][vulnerability['securityVulnerability']['severity']] += 1
                 vulnerability_totals[vulnerability['repository']['url']]['lastUpdate'] = vulnerabilities['defaultBranchRef']['target']['pushedDate']



# Push the latest list of vulnerabilities to the 'CurrentVulnerabilities' tab of the tracking sheet.

total_criticals = 0
total_highs = 0
total_moderates = 0

vulnerability_scores = []

for repo in vulnerability_totals:
    repo_score = ((vulnerability_totals[repo]['CRITICAL']*10) + (vulnerability_totals[repo]['HIGH']*5) + (vulnerability_totals[repo]['MODERATE']*1))
    vulnerability_scores.append([str(repo),vulnerability_totals[repo]['CRITICAL'],vulnerability_totals[repo]['HIGH'],vulnerability_totals[repo]['MODERATE'],repo_score,vulnerability_totals[repo]['lastUpdate']])
    total_criticals = total_criticals + vulnerability_totals[repo]['CRITICAL']
    total_highs = total_highs + vulnerability_totals[repo]['HIGH']
    total_moderates = total_moderates + vulnerability_totals[repo]['MODERATE']


update_datadog(vulnerability_scores)

