from scapy.all import show_interfaces, get_if_list, Conf

print("--- Scapy Interfaces ---")
show_interfaces()

print("\n--- Interface List ---")
print(get_if_list())
