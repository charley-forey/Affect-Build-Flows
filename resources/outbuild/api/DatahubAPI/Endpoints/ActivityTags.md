<!-- Source: https://pp-docs.outbuild.com/docs/DatahubAPI/Endpoints/ActivityTags -->

# ActivityTags

The endpoints described in this section retrieve information on activity tags associated with active schedules in your organization.

# Activity Tags

1. [Endpoint 1: GET all activity tags](#request-activitytags)

## `GET` /activitytags

### Description

*This endpoint retrieves a list of and organization's activity tags.*

> **📄 Pagination**: The endpoint returns **500** activity tags per request  
> **📉 Sorting**: Items are returned sorted by createdAt in descending order (highest to lowest).

### Request

To make a request to an endpoint, use the following URL along with the `authorizationToken` header:

| URL | Headers | Query Params (Optional) |
|---|---|---|
| `https://datahub.outbuild.com/activitytags?page=1` | `authorizationToken` | `page` |

> *🔐 Check [Introduction](https://pp-docs.outbuild.com/docs/DatahubAPI/Introduction) section to learn how you can obtain your unique authorization token.*

This endpoint accepts an optional `page` query parameter. For example, to request the second page of data, use the following URL: `https://datahub.outbuild.com/activitytags?page=2`.

If no `page` parameter is specified (e.g., `https://datahub.outbuild.com/activitytags`), the first page will be returned by default.

### Response

#### 🎉 Success

The endpoint returns a JSON object containing a list of activity tags for a specific organization. If no activity tags are available, the response body will be empty (`[]`).

##### Example response

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "page": 1,
    "hasNextPage": true,
    "activity_tags": [
      {
        "activity_id": 39727,
        "tag_id": 12,
        "project_id": 10961,
        "schedule_id": 42200,
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
  
  - If `true`, additional data, corresponding to next page (`page + 1`) exists.
  - If `false`, no more matching data exists, and subsequent pages will return an empty list (`[]`).

You can find information about each data field in the sections below.

**Click to view a detailed explanation of the fields for each activityTag**

| Name | Description | Type |
|---|---|---|
| `activity_id` | Identifier of the activity to which the tag is associated | Number |
| `tag_id` | Identifier of the tag | Number |
| `project_id` | Identifier of the associated project | Number |
| `schedule_id` | Identifier of the schedule to which the RFV belongs to | Number |

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

Where the error codes and the error messages are as follows:

| `ERROR_CODE` | `ERROR_MESSAGE` | Explanation |
|---|---|---|
| 401 | Unauthorized access: required auth information is missing from the request. | Insufficient authorization data was provided |
| 401 | Unauthorized access: organization id is invalid or is not permitted. | The token does not correspond to a valid organization |
| 401 | Unauthorized access: user role is invalid or is not permitted. | The token does not grant sufficient access permissions |
| 401 | Unauthorized access: user id is invalid or is not permitted. | The token does not correspond to a valid user |
| 500 | Unknown error occurred while processing the request. | The query could not be executed correctly due to a failed database connection or another issue |

If you receive any other message or error code, please retry the request or contact support.

### Example request using cURL

Use the following curl example to connect to the production endpoint (substitute {activityId} with an integer value):

```bash
curl -X GET "https://datahub.outbuild.com/activitytags?page=1" \
   -H "authorizationToken: YOUR_TOKEN_GOES_HERE" \
   -H "Content-Type: application/json"
```
