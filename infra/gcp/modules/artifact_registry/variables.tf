variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "location" {
  type        = string
  description = "Region for Artifact Registry (e.g., us-central1)."
  default     = "us-central1"
}

variable "repository_id" {
  type        = string
  description = "Repository ID."
  default     = "platform-images"
}

variable "format" {
  type        = string
  description = "Repository format."
  default     = "DOCKER"
}

variable "description" {
  type        = string
  description = "Repository description."
  default     = "Docker images for platform services."
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply."
  default     = {}
}
