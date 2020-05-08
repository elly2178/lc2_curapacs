#include <string>  
#include <iostream>

void deleteme()
{  
  for (uint16_t i = 0; i < 1; i++)
  {  
    uint16_t  taggroup = 0x10;
    const char* json = std::to_string(taggroup).c_str();
    std::cout << json;
  }
  return;
}

int main() {
    deleteme();
}