terraform {
  backend "s3" {
    key          = "auth/prod/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
