#!/usr/bin/env python3
"""
批量生成跨境电商买卖对话数据
使用已有对话作为模板，生成变体
"""
import json
import random

# 产品列表
products = [
    "TWS耳机", "手机壳", "LED灯泡", "充电宝", "蓝牙音箱",
    "智能手表", "USB数据线", "无线充电器", "笔记本支架", "摄像头",
    "机械键盘", "游戏鼠标", "耳机支架", "USB风扇", "LED台灯",
    "平板支架", "手机支架", "蓝牙耳机", "智能手环", "电子秤",
    "加湿器", "空气净化器", "投影仪", "智能插座", "路由器",
    "移动硬盘", "U盘", "读卡器", "扩展坞", "HDMI线"
]

# 买家开场白模板
buyer_openers = [
    "你好，我想批量采购{product}，请问你们的单价多少钱？MOQ是多少？I'm an overseas buyer，希望能给个competitive price。",
    "Hi，我是跨境卖家，想采购一批{product}。请问有什么款式/规格？bulk order 500pcs以上什么价格？",
    "你好老板，我想采购{product}，请问有CE/FCC认证吗？MOQ多少，500pcs和1000pcs分别什么价格？",
    "Hello，I'm looking for {product} suppliers. 请问你们的产品质量怎么样？有没有warranty？价格能报一下吗？",
    "你好，想问下{product}的价格，我是长期采购的，量比较大，能给个best price吗？",
]

# 卖家回复模板
seller_responses = [
    "您好！感谢询价，我们的{product}报价{price}/pc，MOQ {moq}pcs起。产品有CE/FCC认证，质量保证。量大可以再谈，请问您预计采购多少？",
    "Hi亲！{product}现货充足，单价{price}，{moq}pcs起订。支持OEM定制logo，交期7-15天。This is our wholesale price，量大优惠！",
    "您好！我们{product}的报价是{price}/unit，MOQ {moq}。产品通过CE/FCC/RoHS认证，1年质保。If you order 1000+, we can offer better price.",
    "感谢关注！{product}报价{price}，起订{moq}pcs。我们是工厂直销，品质有保障，量大从优，请问您的target quantity是多少？",
]

# 买家砍价模板
buyer_negotiate = [
    "这个价格太贵了！I've seen similar products at {lower_price}. 能不能给个更好的价格？",
    "{price}还是有点高，能不能做到{target_price}？如果可以我今天就下单。",
    "价格能不能再便宜点？我是长期买家，量大的话后面还会继续采购。Can you do better?",
    "这个价格没办法接受，别家才{lower_price}。你们能match吗？不然我只能去别家了。",
    "Too expensive! 能不能给个volume discount？如果价格合适我可以加大订单量。",
]

# 卖家让步模板
seller_counter = [
    "亲，{price}真的是我们的底价了，but看在长期合作的份上，我可以给您{new_price}，这已经是best offer了！",
    "这个价格确实很难做，不过如果您quantity能到{moq}以上，我可以申请{new_price}的special price。",
    "Sorry，{target_price}太低了cover不了成本。最低{new_price}，包含free shipping，您看怎么样？",
    "好吧，既然您诚心要，{new_price}成交，but这真的是我们的bottom line了，再低做不了。",
]

# 成交模板
deal_templates = [
    "OK deal! {price}成交，请发PI过来我安排付款。麻烦确认shipping terms和delivery time。",
    "好的，{price}可以接受。Confirmed! 请告知付款方式和发货时间。",
    "Deal! 这个价格OK，请问怎么付款？支持T/T还是PayPal？When can you ship?",
]

def generate_price():
    """生成随机价格"""
    base = random.uniform(3, 50)
    return f"${base:.2f}"

def generate_lower_price(price_str):
    """生成更低的价格"""
    price = float(price_str.replace("$", ""))
    lower = price * random.uniform(0.6, 0.8)
    return f"${lower:.2f}"

def generate_target_price(price_str):
    """生成目标价格"""
    price = float(price_str.replace("$", ""))
    target = price * random.uniform(0.75, 0.9)
    return f"${target:.2f}"

def generate_new_price(price_str, target_str):
    """生成让步后的价格"""
    price = float(price_str.replace("$", ""))
    target = float(target_str.replace("$", ""))
    new = (price + target) / 2
    return f"${new:.2f}"

def generate_dialogue(dialogue_id, product):
    """生成一个完整的对话"""
    dialogues = []

    price = generate_price()
    moq = random.choice([50, 100, 200, 500])

    # Round 1: 买家询价
    buyer_msg = random.choice(buyer_openers).format(product=product)
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 1,
        "role": "buyer",
        "content": buyer_msg
    })

    # Round 1: 卖家回复
    seller_msg = random.choice(seller_responses).format(
        product=product, price=price, moq=moq
    )
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 1,
        "role": "seller",
        "content": seller_msg
    })

    # Round 2: 买家砍价
    lower_price = generate_lower_price(price)
    target_price = generate_target_price(price)
    buyer_msg2 = random.choice(buyer_negotiate).format(
        price=price, lower_price=lower_price, target_price=target_price
    )
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 2,
        "role": "buyer",
        "content": buyer_msg2
    })

    # Round 2: 卖家让步
    new_price = generate_new_price(price, target_price)
    seller_msg2 = random.choice(seller_counter).format(
        price=price, target_price=target_price, new_price=new_price, moq=moq*2
    )
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 2,
        "role": "seller",
        "content": seller_msg2
    })

    # Round 3: 成交
    deal_msg = random.choice(deal_templates).format(price=new_price)
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 3,
        "role": "buyer",
        "content": deal_msg
    })

    # Round 3: 卖家确认
    confirm_msg = f"Great! 确认订单{product} @ {new_price}/pc。请提供shipping address，我这边安排发PI给您。Thank you for your business!"
    dialogues.append({
        "id": dialogue_id,
        "product": product,
        "round": 3,
        "role": "seller",
        "content": confirm_msg
    })

    return dialogues

def main():
    from pathlib import Path
    data_file = Path(__file__).parent.parent / "data" / "dialogue_data.jsonl"

    all_dialogues = []

    # 读取已有数据
    existing_count = 0
    try:
        with open(data_file, "r") as f:
            existing_count = sum(1 for _ in f)
    except:
        pass

    print(f"已有数据: {existing_count} 条")

    # 生成新对话，每个产品生成多个对话
    dialogue_id = 100  # 从100开始，避免与手动生成的冲突
    target = 2000 - existing_count

    while len(all_dialogues) < target:
        product = random.choice(products)
        dialogues = generate_dialogue(dialogue_id, product)
        all_dialogues.extend(dialogues)
        dialogue_id += 1

    # 追加到文件
    with open(data_file, "a") as f:
        for d in all_dialogues[:target]:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"新增数据: {min(len(all_dialogues), target)} 条")
    print(f"总计: {existing_count + min(len(all_dialogues), target)} 条")

if __name__ == "__main__":
    main()
