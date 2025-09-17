import string
from django import template


register = template.Library()


# Регистрируем наш фильтр под именем currency, чтоб Django понимал,
# что это именно фильтр для шаблонов, а не простая функция.
@register.filter()
def currency(text, bword="новость"):
    text_list = text.split()
    censored_text = []
    for word in text_list:
        clean_word = ''.join(c for c in word if c not in string.punctuation)
        if clean_word.lower() in bword:
            censored_word = clean_word[0] + (len(clean_word) - 1) * '*'
            censored_text.append(word.replace(clean_word, censored_word))

        else:
            censored_text.append(word)
    return ' '.join(censored_text)