variable "region" {
  type    = string
  default = "us-east-1"
}

variable "ami" {
  description = "AMI ID for the EC2 instance (default set for us-east-1)"
  type        = string
  default     = "ami-0532be01f26a3de55"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "notification_email" {
  description = "Email address to subscribe to SNS topic alerts"
  type        = string
  default     = "ridwanadewusi3@gmail.com"
}