import random

def generate_saba(max_width=5, max_height=5, probability=0.5):
    head = 'SabaPing'
    body = 'tgm3SABA1'
    tail = 'tgm3SABA2'
    empty = 'tgm300'
    
    final_list = []

    for h in range(max_height):
        line = []
        for w in range(max_width):
            # last row, probability not matter, just finish head/body with tail
            if h == max_height-1:
                if final_list[h-1][w] in [head, body]:
                    line.append(tail)
                else:
                    line.append(empty)
                continue

            # first row, hit -> head, not hit -> empty
            if h == 0:
                if random.random() < probability:
                    line.append(head)
                else:
                    line.append(empty)
                continue
                
            # other row
            # hit
            if random.random() < probability:
                # h-1 is empty/tail
                if final_list[h-1][w] in [empty, tail]:
                    line.append(head)
                # h-1 is head/body
                elif final_list[h-1][w] in [head, body]:
                    line.append(body)

            # not hit
            else:
                # first row
                if h == 0:
                    line.append(empty)
                # other row
                else:
                    if final_list[h-1][w] in [head, body]:
                        line.append(tail)
                    else:
                        line.append(empty)

        final_list.append(line)
    
    return final_list
        

if __name__ == '__main__':
    list = generate_saba()
    print list
    with open('saba.txt', 'w') as f:
        for line in list:
            f.write(' '.join(line)+'\n')
