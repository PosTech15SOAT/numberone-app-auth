terraform {
  backend "s3" {
    key          = "auth/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
