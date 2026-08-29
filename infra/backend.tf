terraform {
  backend "s3" {
    key          = "auth/hml/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
