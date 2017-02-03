# gcp-audit

A tool for auditing security properties of GCP projects. Inspired by [Scout2].

`gcp-audit` takes a set of projects and audits them for common issues as defined by its ruleset. Issues
can include, but are certainly not limited to, storage buckets with read/write permissions for anyone and
compute engine instances with services exposed to the Internet.

The results are written to a report containing information about issues that were found along with information
about which objects these issues were found in so that it's possible to address the problems.

[Scout2]: <https://github.com/nccgroup/Scout2>

`gcp-audit` is currently in alpha status.
We are actively improving it and Spotify's production environment is our
current test suite.

## Installation

Run `pip install git+https://github.com/spotify/gcp-audit.git`.

## Usage

```bash
usage: gcp-audit.py [-h] [-c CHECKS] [-k KEYFILE] [-o OUTPUT] [-p PROJECTS]

A tool for auditing security properties of GCP projects.

optional arguments:
  -h, --help            show this help message and exit
  -c CHECKS, --checks CHECKS
                        comma separated list of types of checks to run
  -k KEYFILE, --keyfile KEYFILE
                        keyfile to use for GCP credentials
  -o OUTPUT, --output OUTPUT
                        file to output results to
  -p PROJECTS, --projects PROJECTS
                        comma separated list of GCP projects to audit
```

## Prerequisites

Make sure you have virtualenv (on OSX: `brew install virtualenv`) then run
```bash
virtualenv env
env/bin/pip install gcp-audit
GOOGLE_APPLICATION_CREDENTIALS=YourCredentials-abc123.json env/bin/python gcp-audit
```

Alternatively you can specify your credentials using the `-k` switch.
Make sure your credentials have the `Organization viewer` role.

Supported Python versions: 2.7+

## Development

To contribute and develop, clone the project inside a virtualenv and install
all the dependencies with `pip install -r requirements.txt`.

## Rules

Rules are put in a [subdirectory] under `rules/`. The subdirectories are based on the check category. Currently checks for the following categories exist:
- `bucket_objects` - objects within buckets (as opposed to the buckets themselves)
- `buckets` - buckets. :)
- `firewalls` - GCP firewall settings
- `cloudsql` - CloudSQL instances

The rule language is fairly simplistic and can be done using YAML (which will be translated to JSON internally) or raw JSON. Each rule can specify the following:
- `name` - the name of the rule that will be shown in reports etc.
- `filters` - a list of filters that the engine should use to match the rule to the object that is being evaluated. This section needs a set of subproperties defined, see below.
  - `matchtype` - specifies how the engine should match filter properties. Valid values are "regex", "exact", "partial" and "count". See the "Match types" section below for more details.
  - `filter` - a template of properties and values that will be matched against the object. The structure of the filter needs to mimic the structure of the object.
  - `listcondition` (OPTIONAL) - what boolean operator to apply if a rule specifies lists with values. Can be "and" or "or". "and" means all list entries must match. "or" means at least one list entry must match.
- `filtercondition` (OPTIONAL) - what boolean operator to apply between multiple filters. Can be "and" or "or". "and" means all filters must match. "or" means at least one list entry must match. Default is "and".

Rules will match against output received from the API's Google exposes for each service supported by gcp-audit. The official documentation on the API's can be found [here] but to make writing rules easier, sample objects for each category are provided in the `docs/samples` directory. As an example of what a rule can look like, this rule will find CloudSQL instances that are exposed to `0.0.0.0/0`:

[subdirectory]: https://github.com/spotify/gcp-audit/tree/master/gcp_audit/rules
[here]: https://developers.google.com/api-client-library/python/apis/

```json
{
    "name": "Traffic allowed from all IP's to CloudSQL instance",
    "filters": [{
        "matchtype": "exact",
        "filter": {
          "settings":{
            "ipConfiguration":{
              "authorizedNetworks":[{
                "value":"0.0.0.0/0"
              }]
            }
          }
        }
    }]
}
```

And here's the same rule in YAML format:
```
name: Traffic allowed from all IP's to CloudSQL instance
filters:
  - matchtype: exact
    filter:
      settings:
        ipConfiguration:
          authorizedNetworks:
            - value: 0.0.0.0/0
```

The engine will apply the filters defined in the template to the object and check whether the properties match exactly and the values match according to the defined `matchtype` for each filter.

### Match types
Each filter must define a match type that will be used for evaluating filter values against object values. Each filter can define only one match type, so for rules that need to evaluate something based on multiple match types, separate filters need to be created.

Examples below are all matching this mock object:
```json
{"someproperty":"some text"}
```

#### exact
Match filter values to the corresponding object values exactly.

Example:
```json
{
"name":"Example regex rule",
"filters":[{
  "matchtype":"exact",
  "filter":{
    "someproperty":"some text"
    }
  }]
}
```

#### partial
Match filter values to the corresponding object values by checking if the filter values are a subset of the object values. No wildcards needed, or supported - wildcards will be treated as regular characters so should only be used if you actually *want* to match a literal `*`.

Example:
```json
{
"name":"Example partial rule",
"filters":[{
  "matchtype":"partial",
  "filter":{
    "someproperty":"me tex"
    }
  }]
}
```

#### regex
Match filter values to the corresponding object values based on regular expressions.

Example:
```json
{
"name":"Example regex rule",
"filters":[{
  "matchtype":"regex",
  "filter":{
    "someproperty":"^.+?so?e\s+text\s*"
    }
  }]
}
```

#### numeric
Perform a numeric comparison between the filter value and the object value. The syntax is `"field":"<op> <value>"` where `op` is one of `eq`, `lt`, `le`, `gt` or `ge`.

Example:
```json
{
"name":"Example numeric rule",
"filters":[{
  "matchtype":"numeric",
  "filter":{
    "someproperty":"lt 100"
    }
  }]
}
```

#### count
This match type doesn't actually look at the data in the fields themselves but rather counts how many occurrences are found of the field that is to be matched. Syntax is identical to the one used for the `numeric` match type, see previous section.

Example:
```json
{
"name":"Example count rule",
"filters":[{
  "matchtype":"count",
  "filter":{
    "someproperty":"ge 1"
    }
  }]
}
```

### Caveats
When writing rules, it's important to remember that the filter template needs to match the object EXACTLY. If a value exists within a list in the object, the template needs to reflect that too. So for the following object:
```json
{"name":"someobject","properties":[{"someproperty":"somevalue"}]}
```

The following template will NOT match, because the subsection under "properties" is not specified as a list:
```json
{"properties":{"someproperty":"somevalue"}}
```

But this one matches:
```json
{"properties":[{"someproperty":"somevalue"}]}
```

Handling both these templates so they both match in an unambiguous way is on the todo list.


## Code of Conduct
This project adheres to the [Open Code of Conduct][code-of-conduct].
By participating, you are expected to honor this code.

[code-of-conduct]: https://github.com/spotify/code-of-conduct/blob/master/code-of-conduct.md
