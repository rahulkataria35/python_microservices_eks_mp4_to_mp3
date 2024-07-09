# python_microservices_eks_mp4_to_mp3


Video Upload and Initial Request Handling:

A user uploads a video to convert it into an MP3.
The request first hits the API Gateway.
Storing Video and Queuing for Processing:

The API Gateway stores the video in MongoDB.
It then places a message on a queue, notifying downstream services that there is a video to be processed in MongoDB.
Video to MP3 Conversion:

The Video to MP3 service consumes messages from the queue.
It retrieves the video ID from the message, pulls the video from MongoDB, converts it to MP3, and stores the MP3 in a different collection in MongoDB.
It then places a new message in the queue for the Notification service, indicating that the conversion job is complete.
Notification Service:

The Notification service consumes messages from the queue.
It emails the client to inform them that the video they uploaded has been converted to MP3 and is ready for download.
Client Download Request:

The client uses a unique ID provided by the Notification service and a JWT to make a request to the API Gateway to download the MP3.
The API Gateway pulls the MP3 from MongoDB and serves it to the client.