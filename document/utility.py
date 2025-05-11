import hashlib
import torch
from random import randint
from transformers import AutoTokenizer, AutoModelForMaskedLM

def link_generator(seed: str, link_length: int =12):
    """
    generate a link of lowercase alphabets with length link_length using MD5
    
    seed (str): The input string to hash
    
    link_length (int): link length
        
    """
    
    md5_hash = hashlib.md5(seed.encode()).hexdigest()
    
    alphabet_hash = []
    for char in md5_hash:
        if char.isdigit():
            alphabet_hash.append(chr(int(char)+97))
        else:
            alphabet_hash.append(char.lower())
    
    full_hash = ''.join(alphabet_hash)
    
    # If we need more characters, cycle through the hash
    if link_length > len(full_hash):
        needed_character = link_length - len(full_hash)
        characters = []
        for _ in range(needed_character):
            characters.append(chr(randint(97,122)))
        link = full_hash + ''.join(characters)
    else:
        link = full_hash[:link_length]
        
    return link



def add_dash(link: str, dash_interval: int = 3):
    """
    add dashes to generated link
    
    link (str): generated link
    
    dash_interval (int): dashing interval
    """
    dash_interval+=1
    link_list = list(link)
    
    for i in range(dash_interval,len(link)+ dash_interval,dash_interval):
        link_list.insert(i-1,'-')
    
    return ''.join(link_list)

def remove_dash(link: str):
    return link.replace('-','')



def suggest_next_words(input: str ) -> list:
    model_name = "HooshvareLab/bert-fa-base-uncased"  # Official ParsBERT
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForMaskedLM.from_pretrained(model_name)
    inputs = tokenizer(f'{input}[MASK]', return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        
    predictions = outputs.logits[0, :].softmax(dim=-1)
    masked_index = torch.where(inputs["input_ids"][0] == tokenizer.mask_token_id)[0]
    predicted_token_ids = torch.topk(predictions[masked_index], k=5).indices.tolist()
    
    result = []
    for token_id in predicted_token_ids[0]:
        word = tokenizer.decode([token_id])
        if word in ["...","?",".","!","؟"]:
            continue
        else:
            result.append(word)
    return result

if __name__ == '__main__':
    test_link = link_generator('1,2,3,4')
    print(test_link)
    print(add_dash(test_link))
    print(remove_dash(add_dash(test_link)))
    
    test_text = input()
    result = suggest_next_words(test_text)
    print(result)