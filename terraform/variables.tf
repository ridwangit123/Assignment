variable "region" {
  type    = string
  default = "us-east-1"
}

variable "ami" {
  description = "AMI ID for the EC2 instance (provide a linux AMI for your region)"
  type        = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}