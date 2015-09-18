#!/bin/bash -x
for i in * ;
do  
  if [ ! -d  ${i} ]; 
  then 
    echo "${i} is not a dir"
    sed -i ".sed" -e 's/electrumdash/encompass/g'  -e 's/electrum-dash/encompass/g' -e 's/Electrum-DASH/Encompass/g'   ${i}
  else 
    cd ${i} 
    for x in * 
    do 
      sed -i ".sed" -e 's/electrumdash/encompass/g'  -e 's/electrum-dash/encompass/g' -e 's/Electrum-DASH/Encompass/g' ${x} 
    done
    cd ..
  fi
done
