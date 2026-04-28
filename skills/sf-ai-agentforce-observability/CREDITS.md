# Credits & Dependencies

## Core Dependencies

### Data Processing

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| [Polars](https://pola.rs/) | >=1.0.0 | MIT | High-performance DataFrame library with lazy evaluation |
| [PyArrow](https://arrow.apache.org/docs/python/) | >=15.0.0 | Apache 2.0 | Parquet file format support and columnar processing |
| [Pydantic](https://docs.pydantic.dev/) | >=2.6.0 | MIT | Data validation and settings management |

### Authentication

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| [PyJWT](https://pyjwt.readthedocs.io/) | >=2.8.0 | MIT | JWT token generation for Salesforce auth |
| [cryptography](https://cryptography.io/) | >=42.0.0 | Apache 2.0 / BSD | Certificate handling for JWT Bearer flow |

### HTTP & CLI

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| [httpx](https://www.python-httpx.org/) | >=0.27.0 | BSD | Modern async HTTP client for Data Cloud API |
| [Click](https://click.palletsprojects.com/) | >=8.1.0 | BSD | CLI framework |
| [Rich](https://rich.readthedocs.io/) | >=13.0.0 | MIT | Terminal formatting, progress bars, tables |

## Salesforce APIs Used

| API | Version | Purpose |
|-----|---------|---------|
| Data Cloud Query API | v60.0+ | Execute SQL queries against DMOs |
| Data Cloud Profile API | v60.0+ | Retrieve metadata about DMOs |
| OAuth 2.0 JWT Bearer | - | Server-to-server authentication |

## Related Salesforce Documentation

- [Data Cloud Query API](https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_query.htm)
- [Agentforce Session Tracing](https://help.salesforce.com/s/articleView?id=sf.copilot_session_tracing.htm)
- [JWT Bearer Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm)

## Inspiration & Patterns

- **sf-data skill**: Data extraction patterns and validation scoring
- **sf-connected-apps skill**: JWT authentication templates
- **sf-ai-agentforce-testing skill**: Agentforce integration patterns

## Acknowledgments

| Contributor | Role | Contribution |
|-------------|------|--------------|
| **Alejandro Raigon** | Forward Deployed Engineer Director, Anthropic | Domain expertise on Agentforce observability patterns, Session Tracing data model insights, and quality analysis approaches |

## License

This skill is released under the MIT License.

```
MIT License

Copyright (c) 2024-2026 Jag Valaiyapathy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
