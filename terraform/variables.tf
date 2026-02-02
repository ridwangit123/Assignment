variable "region" {
  type    = string
  default = "us-east-1"
}

variable "ami" {
  description = "ami-0532be01f26a3de55"
  type        = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}