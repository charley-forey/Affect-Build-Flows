<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/Tags -->

# Tags

The endpoints described in this section retrieve information on tags associated in your organization.

# Tags

1. [Endpoint 1: GET all tags](#request-tags)
2. [Endpoint 2: GET all tags for a specific project](#request-tagsprojectprojectid)
3. [Endpoint 3: GET all tags for a specific project and schedule](#request-tagsprojectprojectidschedulescheduleid)

## `GET` /tags

### Description

*This endpoint retrieves a list of an organization's tags.*

> **📄 Pagination**: The endpoint returns **500** tags per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/tags?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/tags?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/tags`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of tags for a specific organization. If no tags are available, the response body will be empty (`[]`).

##### Example response

```json
  {
    "statusCode": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "page":1,
      "hasNextPage": true,
      "tags": [
        {
          "id": 12,
          "name": "Phase B",
          "description": "#236CF2",
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "project_id": 9,
        }
      ... // more objects with the same structure
      ]
    }
  }
```

#### Properties overview

As the endpoint **is paginated**, the response additionally includes the following fields:

- **`page`**: Indicates the current page number that was either provided in the request URL or defaulted to 1.
- **`hasNextPage`**: Indicates if there are more pages of data present in the database.
  
  - If `true`, aditional data, corresponding to next page (`page + 1`) exists.
  - If `false`, no more matching data exists, and subsequent pages will return an empty list (`[]`).

You can find information about each data field in the sections below.

**Click to view a detailed explanation of the fields for each rfv**

| Name | Description | Type |
|---|---|---|
| `id` | Unique tag identifier | Number |
| `name` | Name associated with the tag | Text |
| `description` | Tags description, corresponding to its associated color | Text |
| `created_at` | Timestamp indicating when the tag was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the tga was last updated | Date in UTC (Zulu Zone) |
| `project_id` | Identifier of the project to which the tag belongs to | Number |

#### ⚠️Failure

The endpoint will return the following response if the request fails:

```json
  {
    "status" : ERROR_CODE,
    "body": {
      "message": ERROR_MESSAGE
    }
  }
```

Where the error codes and the errores messages are as follows:

| `ERROR_CODE` | `ERROR_MESSAGE` | Explanation |
|---|---|---|
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/tags?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```

## `GET` /tags/project/{projectId}

### Description

*This endpoint retrieves a list of an organization's users for a specific project.*

> **📄 Pagination**: The endpoint returns **500** users per request  
> **📉 Sorting**: Items are returned sorted by ID in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/users/project/{projectId}?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/users/project/13?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/users/project/13`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of users for a specific organization and project. If no users are available for the specific project or it doesn't exist, the response body will be empty (`[]`).

##### Example response

```json
  {
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
    "body": {
      "page":1,
      "hasNextPage": true,
      "tags": [
        {
          "id": 12,
          "name": "Phase B",
          "description": "#236CF2",
          "created_at": "2016-03-05 19:23:33.947Z",
          "updated_at": "2023-01-06 15:10:23.890Z",
          "project_id": 9,
        }
      ... // more objects with the same structure
      ]
    }
}
```

#### Properties overview

As the endpoint **is paginated**, the response additionally includes the following fields:

- **`page`**: Indicates the current page number that was either provided in the request URL or defaulted to 1.
- **`hasNextPage`**: Indicates if there are more pages of data present in the database.
  
  - If `true`, aditional data, corresponding to next page (`page + 1`) exists.
  - If `false`, no more matching data exists, and subsequent pages will return an empty list (`[]`).

You can find information about each data field in the sections below.

**Click to view a detailed explanation of the fields for each rfv**

| Name | Description | Type |
|---|---|---|
| `id` | Unique tag identifier | Number |
| `name` | Name associated with the tag | Text |
| `description` | Tags description, corresponding to its associated color | Text |
| `created_at` | Timestamp indicating when the tag was created | Date in UTC (Zulu Zone) |
| `updated_at` | Timestamp indicating when the tga was last updated | Date in UTC (Zulu Zone) |
| `project_id` | Identifier of the project to which the tag belongs to | Number |

#### ⚠️Failure

The endpoint will return the following response if the request fails:

```json
  {
    "status" : ERROR_CODE,
    "body": {
      "message": ERROR_MESSAGE
    }
  }
```

Where the error codes and the errores messages are as follows:

| `ERROR_CODE` | `ERROR_MESSAGE` | Explanation |
|---|---|---|
| 400 | Required URL parameters are either missing from the request or are invalid. | The `projectId` parameter was not provided in the URL or its not a valid integer. |
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint:

```bash
  curl -X GET "https://datahub.outbuild.com/tags/project/{projectId}?page=1" \
     -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
     -H "Content-Type: application/json" \
```
