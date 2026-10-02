terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
    tls = { source = "hashicorp/tls", version = "~> 4.0" }
  }
  backend "azurerm" {}
}
provider "azurerm" { features {} }
variable "location" { default = "eastus" }
resource "azurerm_resource_group" "app" {
  name = "rg-lozas-demo"
  location = var.location
}
resource "azurerm_virtual_network" "app" {
  name = "lozas-vnet"
  resource_group_name = azurerm_resource_group.app.name
  location = var.location
  address_space = ["10.20.0.0/16"]
}
resource "azurerm_subnet" "app" {
  name = "default"
  resource_group_name = azurerm_resource_group.app.name
  virtual_network_name = azurerm_virtual_network.app.name
  address_prefixes = ["10.20.1.0/24"]
}
resource "azurerm_public_ip" "app" {
  name = "lozas-ip"
  resource_group_name = azurerm_resource_group.app.name
  location = var.location
  allocation_method = "Static"
  sku = "Standard"
}
resource "azurerm_network_security_group" "app" {
  name = "lozas-nsg"
  resource_group_name = azurerm_resource_group.app.name
  location = var.location
  security_rule {
    name = "HTTP"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "80"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }
}
resource "azurerm_network_interface" "app" {
  name = "lozas-nic"
  resource_group_name = azurerm_resource_group.app.name
  location = var.location
  ip_configuration {
    name = "default"
    subnet_id = azurerm_subnet.app.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id = azurerm_public_ip.app.id
  }
}
resource "azurerm_network_interface_security_group_association" "app" {
  network_interface_id = azurerm_network_interface.app.id
  network_security_group_id = azurerm_network_security_group.app.id
}
resource "tls_private_key" "admin" { algorithm = "RSA" }
resource "azurerm_linux_virtual_machine" "app" {
  name = "vm-lozas"
  resource_group_name = azurerm_resource_group.app.name
  location = var.location
  size = "Standard_B1ms"
  admin_username = "azureuser"
  network_interface_ids = [azurerm_network_interface.app.id]
  admin_ssh_key {
    username = "azureuser"
    public_key = tls_private_key.admin.public_key_openssh
  }
  os_disk {
    caching = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }
  source_image_reference {
    publisher = "Canonical"
    offer = "0001-com-ubuntu-server-jammy"
    sku = "22_04-lts-gen2"
    version = "latest"
  }
  custom_data = base64encode("#cloud-config\npackage_update: true\npackages:\n  - docker.io\n  - git\nruncmd:\n  - systemctl enable --now docker\n")
}
output "application_url" { value = "http://${azurerm_public_ip.app.ip_address}" }
