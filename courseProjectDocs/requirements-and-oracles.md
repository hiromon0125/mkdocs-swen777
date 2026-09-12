## Functional Requirements
1. The system shall gather markdown files from the docs directory
2. The system shall generate url path to the page according to the directory path
3. The system shall use the configuration file located at the root as configuration options
4. The system shall set the title of the webpage when configured with site_name option
5. The system shall set the theme of the webpage when configured with theme option
6. The system shall set the icon of the webpage when an icon image is placed under img directory

## Non-Functional Requirements
1. The system shall build 100 pages within 20 seconds
2. The system shall support screen sizes for desktop, tablet, and mobile 
3. The system shall function identical in all latest versions of web browsers

## Test Oracles

| Requirement ID | Requirement Description                                                                  | Test Oracle(Expected Behavior)                                                                                                          |
| -------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| FR1.1          | The system shall gather markdown files from the docs directory                           | After creating an empty docs/index{0-9}.md file the output should also contain /index{0-9}.html                                         |
| FR1.2          | The system shall gather markdown files from the docs directory                           | After creating an index.md in project root the output should not contain that page                                                      |
| FR2            | The system shall generate url path to the page according to the directory path           | After creating an empty docs/nested1/index.md and docs/nested1/nested2/index.md there should be a page at /nested1 and /nested1/nested2 |
| FR3            | The system shall use the configuration file located at the root as configuration options | After creating mkdocs.yml in project root the output should reflect the configurations                                                  |
| FR4            | The system shall set the title of the webpage when configured with site_name option      | After creating mkdocs.yml with "site_name: test123", the title of the index.md page should be set to "test123".                         |
| NFR1           | The system shall build 100 pages within 20 seconds                                       | After creating docs/test{0-100}.md and running "mkdocs build", the command should complete within 20 seconds                            |
