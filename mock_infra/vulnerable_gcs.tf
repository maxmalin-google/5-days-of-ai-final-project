resource "google_storage_bucket" "vulnerable_bucket" {
  name          = "my-company-public-data-bucket-123"
  location      = "US"
  force_destroy = true
}

# Vulnerability: Setting IAM binding to public (allUsers)
resource "google_storage_bucket_iam_binding" "public_read" {
  bucket = google_storage_bucket.vulnerable_bucket.name
  role   = "roles/storage.objectViewer"

  members = [
    "allUsers",
  ]
}
